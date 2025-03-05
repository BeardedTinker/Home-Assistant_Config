from __future__ import annotations
import io
import logging
import os
import math
import json
import re
import urllib
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from functools import partial

import requests
import qrcode
import base64

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.network import get_url
from .const import DOMAIN, SIGNAL_TAG_IMAGE_UPDATE
from .tag_types import TagType, get_tag_types_manager
from .util import get_image_path
from PIL import Image, ImageDraw, ImageFont
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.util import dt
from datetime import timedelta, datetime

_LOGGER = logging.getLogger(__name__)

# Color constants with alpha channel
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
HALF_BLACK = (127, 127, 127, 255)
RED = (255, 0, 0, 255)
HALF_RED = (255, 127, 127, 255)
YELLOW = (255, 255, 0, 255)
HALF_YELLOW = (255, 255, 127, 255)

class ElementType(str, Enum):
    """Enum for supported element types."""

    TEXT = "text"
    MULTILINE = "multiline"
    LINE = "line"
    RECTANGLE = "rectangle"
    RECTANGLE_PATTERN = "rectangle_pattern"
    POLYGON = "polygon"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    ARC = "arc"
    ICON = "icon"
    DLIMG = "dlimg"
    QRCODE = "qrcode"
    PLOT = "plot"
    PROGRESS_BAR = "progress_bar"
    DIAGRAM = "diagram"
    ICON_SEQUENCE = "icon_sequence"
    DEBUG_GRID = "debug_grid"

    @classmethod
    def required_fields(cls, element_type: 'ElementType') -> list[str]:
        """Get required fields for each element type."""
        return REQUIRED_FIELDS.get(element_type, [])

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

class CoordinateParser:
    """Helper class for parsing coordinates with percentage support."""

    def __init__(self, canvas_width: int, canvas_height: int):
        """Initialize with canvas dimensions."""
        self.width = canvas_width
        self.height = canvas_height

    @staticmethod
    def _parse_dimension(value: str | int | float, total_dimension: int) -> int:
        """Convert a dimension value (pixels or percentage) to absolute pixels.

        Args:
            value: The dimension value (e.g., "50%", 50, "50")
            total_dimension: The total available dimension (width or height)

        Returns:
            int: The calculated pixel value
        """
        if isinstance(value, (int, float)):
            return int(value)

        value = str(value).strip()
        if value.endswith('%'):
            try:
                percentage = float(value[:-1])
                return int((percentage / 100) * total_dimension)
            except ValueError:
                return 0
        try:
            return int(float(value))
        except ValueError:
            return 0

    def parse_x(self, value: str | int | float) -> int:
        """Parse x coordinate value."""
        return self._parse_dimension(value, self.width)

    def parse_y(self, value: str | int | float) -> int:
        """Parse y coordinate value."""
        return self._parse_dimension(value, self.height)

    def parse_size(self, value: str | int | float, is_width: bool = True) -> int:
        """Parse size value."""
        return self._parse_dimension(value, self.width if is_width else self.height)

    def parse_coordinates(self, element: dict, prefix: str = '') -> tuple[int, int]:
        """Parse x,y coordinates from element with given prefix.

        Args:
            element: Element dictionary
            prefix: Optional prefix for coordinate keys (e.g., 'start_' or 'end_')

        Returns:
            tuple: (x, y) coordinates in pixels
        """
        x_key = f"{prefix}x"
        y_key = f"{prefix}y"

        x = self.parse_x(element.get(x_key, 0))
        y = self.parse_y(element.get(y_key, 0))

        return x, y

# Define required fields for each element type
REQUIRED_FIELDS: Dict[ElementType, list[str]] = {
    ElementType.TEXT: ["x", "value"],
    ElementType.MULTILINE: ["x", "value", "delimiter", "offset_y"],
    ElementType.LINE: ["x_start", "x_end"],
    ElementType.RECTANGLE: ["x_start", "x_end", "y_start", "y_end"],
    ElementType.RECTANGLE_PATTERN: [
        "x_start", "x_size", "y_start", "y_size",
        "x_repeat", "y_repeat", "x_offset", "y_offset"
    ],
    ElementType.POLYGON: ["points"],
    ElementType.CIRCLE: ["x", "y", "radius"],
    ElementType.ELLIPSE: ["x_start", "x_end", "y_start", "y_end"],
    ElementType.ARC: ["x", "y", "radius", "start_angle", "end_angle"],
    ElementType.ICON: ["x", "y", "value", "size"],
    ElementType.DLIMG: ["x", "y", "url", "xsize", "ysize"],
    ElementType.QRCODE: ["x", "y", "data"],
    ElementType.PLOT: ["data"],
    ElementType.PROGRESS_BAR: ["x_start", "x_end", "y_start", "y_end", "progress"],
    ElementType.DIAGRAM: ["x", "height"],
    ElementType.ICON_SEQUENCE: ["x", "y", "icons", "size"],
    ElementType.DEBUG_GRID: []
}

def validate_element(element: Dict[str, Any]) -> ElementType:
    """Validate element and return its type."""

    if "type" not in element:
        raise ValueError("Element missing required 'type' field")

    try:
        element_type = ElementType(element["type"])
    except ValueError:
        raise ValueError(f"Invalid element type: {element['type']}")

    # Check required fields
    missing_fields = [
        field for field in REQUIRED_FIELDS[element_type]
        if field not in element
    ]

    if missing_fields:
        raise KeyError(
            f"Element type '{element_type}' missing required fields: {', '.join(missing_fields)}"
        )

    return element_type

@dataclass
class TextSegment:
    """Represents a segment of text with its color."""
    text: str
    color: str
    start_x: int = 0

class ImageGen:
    """Handles custom image generation for ESLs."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the image generator."""
        self.hass = hass
        self._queue = []
        self._running = False
        self._not_setup = True
        self._last_interaction_file = os.path.join(os.path.dirname(__file__), "lastapinteraction.txt")
        # Initialize handler mapping
        self._draw_handlers = {
            ElementType.TEXT: self._draw_text,
            ElementType.MULTILINE: self._draw_multiline,
            ElementType.LINE: self._draw_line,
            ElementType.RECTANGLE: self._draw_rectangle,
            ElementType.RECTANGLE_PATTERN: self._draw_rectangle_pattern,
            ElementType.POLYGON: self._draw_polygon,
            ElementType.CIRCLE: self._draw_circle,
            ElementType.ELLIPSE: self._draw_ellipse,
            ElementType.ARC: self._draw_arc,
            ElementType.ICON: self._draw_icon,
            ElementType.DLIMG: self._draw_downloaded_image,
            ElementType.QRCODE: self._draw_qrcode,
            ElementType.PLOT: self._draw_plot,
            ElementType.PROGRESS_BAR: self._draw_progress_bar,
            ElementType.DIAGRAM: self._draw_diagram,
            ElementType.ICON_SEQUENCE: self._draw_icon_sequence,
            ElementType.DEBUG_GRID: self._draw_debug_grid
        }

    async def get_tag_info(self, entity_id: str) -> Optional[tuple[TagType, str]]:
        """Get tag type information for an entity."""

        try:
            # Get hub instance
            if DOMAIN not in self.hass.data or not self.hass.data[DOMAIN]:
                raise HomeAssistantError("OpenEPaperLink integration not properly configured")

            hub = next(iter(self.hass.data[DOMAIN].values()))
            if not hub.online:
                raise HomeAssistantError("OpenEPaperLink AP is offline")

            # Get tag MAC from entity ID
            try:
                tag_mac = entity_id.split(".")[1].upper()
            except IndexError:
                raise HomeAssistantError(f"Invalid entity ID format: {entity_id}")

            # First check if tag is known to the hub
            if tag_mac not in hub.tags:
                raise HomeAssistantError(
                    f"Tag {tag_mac} is not registered with the AP. "
                    "If the tag has checked in, try restarting Home Assistant."
                )

            # Check if tag is blacklisted
            if tag_mac in hub.get_blacklisted_tags():
                raise HomeAssistantError(
                    f"Tag {tag_mac} is currently blacklisted. Remove it from the blacklist in integration options to use it."
                )

            # Get tag data - should exist since we checked hub.tags
            tag_data = hub.get_tag_data(tag_mac)
            if not tag_data:
                raise HomeAssistantError(
                    f"Inconsistent state: Tag {tag_mac} is known but has no data. "
                    "Please report this as a bug."
                )

            # Get hardware type
            hw_type = tag_data.get("hw_type")
            if hw_type is None:
                raise HomeAssistantError(
                    f"No hardware type found for tag {tag_mac}. "
                    "Please wait for the tag to complete its next check-in."
                )

            # Get tag type information
            tag_manager = await get_tag_types_manager(self.hass)
            tag_type = await tag_manager.get_tag_info(hw_type)

            if not tag_type:
                raise HomeAssistantError(
                    f"Unknown hardware type {hw_type} for tag {tag_mac}. "
                    "Try refreshing tag types from the integration options."
                )
            # Get accent color from tag type's color table if it exists
            # Default to red if no color table or no accent specified
            try:
                color_table = getattr(tag_type, 'color_table', {})
                accent_color = color_table.get("accent", "red") if color_table else "red"
            except Exception as e:
                _LOGGER.warning("Error getting accent color, defaulting to red: %s", e)
                accent_color = "red"
            return tag_type, accent_color

        except Exception as e:
            # Convert any unknown exceptions to HomeAssistantError with context
            if not isinstance(e, HomeAssistantError):
                raise HomeAssistantError(
                    f"Unexpected error getting tag type for {entity_id}: {str(e)}"
                ) from e
            raise

    @staticmethod
    def get_index_color(color: Optional[str], accent_color: str = "red") -> tuple[int, int, int, int] | None:
        """Convert color name to RGBA tuple."""
        if color is None:
            return None
        color_str = str(color).lower()
        if color_str in ("black", "b"):
            return BLACK
        if color_str in ("half_black", "hb", "gray", "grey", "g"):
            return HALF_BLACK
        elif color_str in ("accent", "a"):
            return YELLOW if accent_color == "yellow" else RED
        elif color_str in ("half_accent", "ha"):
            return HALF_YELLOW if accent_color == "yellow" else HALF_RED
        elif color_str in ("red", "r"):
            return RED
        elif color_str in ("half_red", "hr"):
            return HALF_RED
        elif color_str in ("yellow", "y"):
            return YELLOW
        elif color_str in ("half_yellow", "hy"):
            return HALF_YELLOW
        else:
            return WHITE

    @staticmethod
    def should_show_element(element: dict) -> bool:
        """Check if an element should be displayed."""
        return element.get("visible", True)

    @staticmethod
    def check_required_arguments(element: dict, required_keys: list[str], element_type: str) -> None:
        """Validate required arguments are present."""
        missing = [key for key in required_keys if key not in element]
        if missing:
            raise HomeAssistantError(
                f"Missing required argument(s) '{', '.join(missing)}' for {element_type}"
            )

    async def generate_custom_image(
            self,
            entity_id: str,
            service_data: Dict[str, Any],
            error_collector: list = None
    ) -> bytes:
        """Generate a custom image based on service data."""

        error_collector = error_collector if error_collector is not None else []

        tag_type, accent_color = await self.get_tag_info(entity_id)
        if not tag_type:
            raise HomeAssistantError("Failed to get tag type information")

        # Get canvas dimensions from tag type
        canvas_width = tag_type.width
        canvas_height = tag_type.height

        # Get rotation and create base image
        rotate = service_data.get("rotate", 0)
        if rotate in (0, 180):
            img = Image.new('RGBA', (canvas_width, canvas_height),
                            color=self.get_index_color(service_data.get("background", "white"), accent_color))
        else:
            img = Image.new('RGBA', (canvas_height, canvas_width),
                            color=self.get_index_color(service_data.get("background", "white"), accent_color))

        pos_y = 0
        payload = service_data.get("payload", [])

        for i, element in enumerate(payload):
            if not self.should_show_element(element):
                continue

            try:
                # Validate element and get its type
                element_type = validate_element(element)

                # Get the appropriate handler and call it
                handler = self._draw_handlers.get(element_type)
                if handler:
                    pos_y = await handler(img, element, pos_y)
                else:
                    error_msg = f"No handler found for element type: {element_type}"
                    _LOGGER.warning(error_msg)
                    error_collector.append(f"Element {i + 1}: {error_msg}")

            except (ValueError, KeyError) as e:
                error_msg = f"Element {i + 1}: {str(e)}"
                _LOGGER.error(error_msg)
                error_collector.append(error_msg)
                continue
            except Exception as e:
                error_msg = f"Element {i + 1} (type '{element.get('type', 'unknown')}'): {str(e)}"
                _LOGGER.error(error_msg)
                error_collector.append(error_msg)
                continue

        # Apply rotation if needed
        if rotate:
            img = img.rotate(rotate, expand=True)

        # Convert to RGB for JPEG
        rgb_image = img.convert('RGB')

        # Create BytesIO object for the JPEG data
        img_byte_arr = io.BytesIO()
        rgb_image.save(img_byte_arr, format='JPEG', quality="maximum")
        image_data = img_byte_arr.getvalue()

        # Save files in executor
        async def save_files():
            """Save generated image to web directory."""
            web_path = get_image_path(self.hass, entity_id)

            # Ensure directory exists
            os.makedirs(os.path.dirname(web_path), exist_ok=True)

            def _save_file():
                with open(web_path, 'wb') as f:
                    f.write(image_data)

            await self.hass.async_add_executor_job(_save_file)
            async_dispatcher_send(self.hass, f"{SIGNAL_TAG_IMAGE_UPDATE}_{entity_id.split('.')[1].upper()}", False)

        # Start saving files in the background
        self.hass.async_create_task(save_files())

        return image_data

    async def _draw_text(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw (coloured) text with optional wrapping or ellipsis."""
        self.check_required_arguments(element, ["x", "value"], "text")

        draw = ImageDraw.Draw(img)
        draw.fontmode = "1"
        coords = CoordinateParser(img.width, img.height)

        x = coords.parse_x(element['x'])
        if "y" not in element:
            y = pos_y + element.get('y_padding', 10)
        else:
            y = coords.parse_y(element['y'])
        # Get text properties
        size = coords.parse_size(element.get('size', 20), is_width=False)
        font_name = element.get('font', "ppb.ttf")
        font_path = os.path.join(os.path.dirname(__file__), font_name)
        font = ImageFont.truetype(font_path, size)

        # Get alignment and default color
        align = element.get('align', "left")
        default_color = self.get_index_color(element.get('color', "black"))
        anchor = element.get('anchor')
        spacing = element.get('spacing', 5)
        stroke_width = element.get('stroke_width', 0)
        stroke_fill = self.get_index_color(element.get('stroke_fill', 'white'))

        # Process text content
        text = str(element['value'])
        max_width = element.get('max_width')

        # Handle text wrapping if max_width is specified
        final_text = text
        if max_width is not None:
            if element.get('truncate', False):
                if draw.textlength(text, font=font) > max_width:
                    ellipsis = "..."
                    truncated = text
                    while truncated and draw.textlength(truncated + ellipsis, font=font) > max_width:
                        truncated = truncated[:-1]
                    final_text = truncated + ellipsis
            else:
                words = text.split()
                lines = []
                current_line = []

                for word in words:
                    test_line = ' '.join(current_line + [word])
                    if not current_line or draw.textlength(test_line, font=font) <= max_width:
                        current_line.append(word)
                    else:
                        lines.append(' '.join(current_line))
                        current_line = [word]

                if current_line:
                    lines.append(' '.join(current_line))
                final_text = '\n'.join(lines)

        # Set appropriate anchor based on line count
        if not anchor:
            anchor = 'la' if '\n' in final_text else 'lt'

        # Draw the text
        if element.get('parse_colors', False):
            segments = self._parse_colored_text(final_text)
            segments, total_width = self._calculate_segment_positions(
                segments, font, x, align
            )

            max_y = y
            for segment in segments:
                color = self.get_index_color(segment.color, element.get('accent_color', 'red'))
                bbox = draw.textbbox(
                    (segment.start_x, y),
                    segment.text,
                    font=font,
                    anchor=anchor
                )
                draw.text(
                    (segment.start_x, y),
                    segment.text,
                    fill=color,
                    font=font,
                    anchor=anchor,
                    spacing=spacing,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_fill
                )
                max_y = max(max_y, bbox[3])
            return max_y
        else:
            bbox = draw.textbbox(
                (x, y),
                final_text,
                font=font,
                anchor=anchor,
                spacing=spacing,
                align=align
            )
            draw.text(
                (x, y),
                final_text,
                fill=default_color,
                font=font,
                anchor=anchor,
                align=align,
                spacing=spacing,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill
            )
            return bbox[3]

    @staticmethod
    def _get_wrapped_text(text: str, font: ImageFont.ImageFont, line_length: int) -> str:
        """Wrap text to fit within a given width."""
        lines = ['']
        for word in text.split():
            line = f'{lines[-1]} {word}'.strip()
            if font.getlength(line) <= line_length:
                lines[-1] = line
            else:
                lines.append(word)
        return '\n'.join(lines)

    @staticmethod
    def _parse_colored_text(text: str) -> List[TextSegment]:
        """Parse text with color markup into text segments."""

        segments = []
        current_pos = 0
        pattern = r'\[(black|white|red|yellow|accent)\](.*?)\[/\1\]'

        for match in re.finditer(pattern, text):
            # Add any text before the match with default color
            if match.start() > current_pos:
                segments.append(
                    TextSegment(
                        text=text[current_pos:match.start()],
                        color="black"
                    ))
            # Add the matched text with the specified color
            segments.append(
                TextSegment(
                    text=match.group(2),
                    color=match.group(1)
                )
            )
            current_pos = match.end()

        # Add any remaining text with default color
        if current_pos < len(text):
            segments.append(TextSegment(
                text=text[current_pos:],
                color="black"
            ))

        return segments

    @staticmethod
    def _calculate_segment_positions(
            segments: List[TextSegment],
            font: ImageFont.FreeTypeFont,
            start_x: int,
            alignment: str = "left"
    ) -> Tuple[List[TextSegment], int]:
        """Calculate x positions for each text segment based on alignment.
        Returns the modified segments and the total width."""

        total_width = sum(font.getlength(segment.text) for segment in segments)

        current_x = start_x
        match alignment.lower():
            case "left":
                pass  # start_x is already correct
            case "center":
                current_x -= total_width / 2
            case "right":
                current_x -= total_width
            case _:
                # Default to left alignment for unknown values
                _LOGGER.warning("Unknown alignment '%s', defaulting to left", alignment)

        for segment in segments:
            segment.start_x = int(current_x)
            current_x += font.getlength(segment.text)

        return segments, total_width


    async def _draw_multiline(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw multiline text with delimiter."""
        self.check_required_arguments(
            element,
            ["x", "value", "delimiter", "offset_y"],
            "multiline"
        )

        draw = ImageDraw.Draw(img)
        draw.fontmode = "1"

        # Get text properties
        size = element.get('size', 20)
        font_name = element.get('font', "ppb.ttf")
        font_path = os.path.join(os.path.dirname(__file__), font_name)
        font = ImageFont.truetype(font_path, size)
        color = self.get_index_color(element.get('color', "black"))
        anchor = element.get('anchor', "lm")
        stroke_width = element.get('stroke_width', 0)
        stroke_fill = self.get_index_color(element.get('stroke_fill', 'white'))

        # Split text using delimiter
        lines = element['value'].replace("\n", "").split(element["delimiter"])
        current_y = element.get('start_y', pos_y + element.get('y_padding', 10))

        max_y = current_y
        for line in lines:
            draw.text(
                (element['x'], current_y),
                str(line),
                fill=color,
                font=font,
                anchor=anchor,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill
            )
            current_y += element['offset_y']
            max_y = current_y

        return max_y

    async def _draw_line(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw line element."""
        self.check_required_arguments(element, ["x_start", "x_end"], "line")

        draw = ImageDraw.Draw(img)

        # Get vertical position
        if "y_start" not in element:
            y_start = pos_y + element.get("y_padding", 0)
            y_end = y_start
        else:
            y_start = element["y_start"]
            y_end = element.get("y_end", y_start)

        # Get line properties
        fill = self.get_index_color(element.get('fill', "black"))
        width = element.get('width', 1)
        dashed = element.get('dashed', False)
        dash_length = element.get('dash_length', 5)
        space_length = element.get('space_length', 3)

        x_start = element["x_start"]
        x_end = element["x_end"]

        if dashed:
            self._draw_dashed_line(
                draw,
                (x_start, y_start),
                (x_end, y_end),
                dash_length,
                space_length,
                fill, width)
        else:
            draw.line(
                [(element['x_start'], y_start), (element['x_end'], y_end)],
                fill=fill,
                width=width
            )

        return max(y_start, y_end)

    @staticmethod
    def _draw_dashed_line(draw: ImageDraw.ImageDraw,
                                start: tuple[int, int],
                                end: tuple[int, int],
                                dash_length: int,
                                space_length: int,
                                fill: tuple[int, int, int, int] = BLACK,
                                width: int = 1,
                                ) -> None:
        """Draw dashed line."""
        x1, y1 = start
        x2, y2 = end

        dx = x2 - x1
        dy = y2 - y1
        line_length = (dx**2 + dy**2) ** 0.5

        step_x = dx / line_length
        step_y = dy / line_length

        current_pos = 0.0

        while True:
            # 1) Draw a dash segment
            dash_end = current_pos + dash_length

            if dash_end >= line_length:
                # We have a partial dash that ends exactly or beyond the line_end
                dash_end = line_length
                segment_len = dash_end - current_pos

                segment_start_x = x1 + step_x * current_pos
                segment_start_y = y1 + step_y * current_pos
                segment_end_x = x1 + step_x * dash_end
                segment_end_y = y1 + step_y * dash_end

                draw.line(
                    [(segment_start_x, segment_start_y), (segment_end_x, segment_end_y)],
                    fill=fill,
                    width=width
                )
                # We're done, because we've reached the end of the line
                break
            else:
                # Normal full dash
                segment_start_x = x1 + step_x * current_pos
                segment_start_y = y1 + step_y * current_pos
                segment_end_x = x1 + step_x * dash_end
                segment_end_y = y1 + step_y * dash_end

                draw.line(
                    [(segment_start_x, segment_start_y), (segment_end_x, segment_end_y)],
                    fill=fill,
                    width=width
                )

                # 2) Move current_pos forward past this dash
                current_pos = dash_end

            # 3) Skip the space segment
            space_end = current_pos + space_length
            if space_end >= line_length:
                # The space would exceed the line's end, so we're done
                break
            else:
                # Jump over the space
                current_pos = space_end

    @staticmethod
    def _get_rounded_corners(corner_string: str) -> tuple[bool, bool, bool, bool]:
        """Get rounded corner configuration."""
        if corner_string == "all":
            return True, True, True, True

        corners = corner_string.split(",")
        corner_map = {
            "top_left": 0,
            "top_right": 1,
            "bottom_right": 2,
            "bottom_left": 3
        }

        result = [False] * 4
        for corner in corners:
            corner = corner.strip()
            if corner in corner_map:
                result[corner_map[corner]] = True

        return result[0], result[1], result[2], result[3]

    async def _draw_rectangle(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw rectangle element."""
        self.check_required_arguments(
            element,
            ["x_start", "x_end", "y_start", "y_end"],
            "rectangle"
        )

        draw = ImageDraw.Draw(img)
        coords = CoordinateParser(img.width, img.height)

        # Coordinates
        x_start = coords.parse_x(element['x_start'])
        x_end = coords.parse_x(element['x_end'])
        y_start = coords.parse_y(element['y_start'])
        y_end = coords.parse_y(element['y_end'])

        # Get rectangle properties
        rect_fill = self.get_index_color(element.get('fill'))
        rect_outline = self.get_index_color(element.get('outline', "black"))
        rect_width = element.get('width', 1)
        radius = element.get('radius', 10 if 'corners' in element else 0)
        corners = self._get_rounded_corners(
            element.get('corners', "all" if 'radius' in element else "")
        )

        # Draw rectangle
        draw.rounded_rectangle(
            (x_start, y_start, x_end,y_end),
            fill=rect_fill,
            outline=rect_outline,
            width=rect_width,
            radius=radius,
            corners=corners
        )

        return y_end

    async def _draw_rectangle_pattern(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw repeated rectangle pattern."""
        self.check_required_arguments(
            element,
            ["x_start", "x_size", "y_start", "y_size",
             "x_repeat", "y_repeat", "x_offset", "y_offset"],
            "rectangle_pattern"
        )

        draw = ImageDraw.Draw(img)

        # Get pattern properties
        fill = self.get_index_color(element.get('fill'))
        outline = self.get_index_color(element.get('outline', "black"))
        width = element.get('width', 1)
        radius = element.get('radius', 10 if 'corners' in element else 0)
        corners = self._get_rounded_corners(
            element.get('corners', "all" if 'radius' in element else "")
        )

        max_y = element['y_start']

        # Draw rectangle grid
        for x in range(element["x_repeat"]):
            for y in range(element["y_repeat"]):
                # Calculate rectangle position
                x_pos = element['x_start'] + x * (element['x_offset'] + element['x_size'])
                y_pos = element['y_start'] + y * (element['y_offset'] + element['y_size'])

                # Draw individual rectangle
                draw.rounded_rectangle(
                    (x_pos, y_pos,
                     x_pos + element['x_size'],
                     y_pos + element['y_size']),
                    fill=fill,
                    outline=outline,
                    width=width,
                    radius=radius,
                    corners=corners
                )

                max_y = max(max_y, y_pos + element['y_size'])

        return max_y

    async def _draw_polygon(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw a polygon."""
        self.check_required_arguments(element, ["points"], "polygon")

        draw = ImageDraw.Draw(img)

        # Parse vertices
        coords = CoordinateParser(img.width, img.height)
        vertices = [
            (coords.parse_x(x), coords.parse_y(y))
            for x, y in element["points"]
        ]

        # Get polygon properties
        fill = self.get_index_color(element.get("fill"))
        outline = self.get_index_color(element.get("outline", "black"))
        width = element.get("width", 1)

        # Draw the polygon
        draw.polygon(vertices, fill=fill, outline=outline)

        return pos_y

    async def _draw_circle(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw circle element."""
        self.check_required_arguments(
            element,
            ["x", "y", "radius"],
            "circle"
        )

        draw = ImageDraw.Draw(img)
        coords = CoordinateParser(img.width, img.height)

        # Coordinates
        x = coords.parse_x(element['x'])
        y = coords.parse_y(element['y'])


        # Get circle properties
        fill = self.get_index_color(element.get('fill'))
        outline = self.get_index_color(element.get('outline', "black"))
        width = element.get('width', 1)

        # Draw circle
        draw.ellipse(
            [(x - element['radius'], y - element['radius']), (x+ element['radius'], y + element['radius'])],
            fill=fill,
            outline=outline,
            width=width
        )

        return y + element['radius']

    async def _draw_ellipse(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw ellipse element."""
        self.check_required_arguments(
            element,
            ["x_start", "x_end", "y_start", "y_end"],
            "ellipse"
        )

        draw = ImageDraw.Draw(img)
        coords = CoordinateParser(img.width, img.height)

        # Coordinates
        x_start = coords.parse_x(element['x_start'])
        x_end = coords.parse_x(element['x_end'])
        y_start = coords.parse_y(element['y_start'])
        y_end = coords.parse_y(element['y_end'])

        # Get ellipse properties
        fill = self.get_index_color(element.get('fill'))
        outline = self.get_index_color(element.get('outline', "black"))
        width = element.get('width', 1)

        # Draw ellipse
        draw.ellipse(
            [(x_start, y_start), (x_end, y_end)],
            fill=fill,
            outline=outline,
            width=width
        )

        return y_end

    async def _draw_arc(self, img: Image, element: dict, pos_y: int):
        """Draw an arc or pie slice."""
        self.check_required_arguments(
            element,
            ["x", "y", "radius", "start_angle", "end_angle"],
            "arc"
        )

        draw = ImageDraw.Draw(img)
        coords = CoordinateParser(img.width, img.height)

        # Parse center coordinates and radius
        x = coords.parse_x(element["x"])
        y = coords.parse_y(element["y"])
        radius = coords.parse_size(element["radius"], is_width=True)

        # Parse angles
        start_angle = element["start_angle"]
        end_angle = element["end_angle"]

        # Calculate bounding box of the circle/ellipse
        bbox = [
            (x - radius, y - radius),
            (x + radius, y + radius)
        ]

        # Get arc properties
        fill = self.get_index_color(element.get("fill"))  # Used for pie slices
        outline = self.get_index_color(element.get("outline", "black"))
        width = element.get("width", 1)

        # Draw the arc
        if fill:
            # Filled pie slice
            draw.pieslice(
                bbox,
                start=start_angle,
                end=end_angle,
                fill=fill,
                outline=outline
            )
        else:
            # Outline-only arc
            draw.arc(
                bbox,
                start=start_angle,
                end=end_angle,
                fill=outline,
                width=width
            )

        return pos_y

    async def _draw_icon(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw Material Design Icons."""
        self.check_required_arguments(
            element,
            ["x", "y", "value", "size"],
            "icon"
        )

        draw = ImageDraw.Draw(img)
        draw.fontmode = "1"  # Enable high quality font rendering
        coords = CoordinateParser(img.width, img.height)

        # Coordinates
        x = coords.parse_x(element['x'])
        y = coords.parse_y(element['y'])


        # Load MDI font and metadata
        font_file = os.path.join(os.path.dirname(__file__), 'materialdesignicons-webfont.ttf')
        meta_file = os.path.join(os.path.dirname(__file__), "materialdesignicons-webfont_meta.json")

        try:
            def load_meta():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            mdi_data = await self.hass.async_add_executor_job(load_meta)
        except Exception as e:
            raise HomeAssistantError(f"Failed to load MDI metadata: {str(e)}")

        # Find icon codepoint
        icon_name = element['value']
        if icon_name.startswith("mdi:"):
            icon_name = icon_name[4:]

        chr_hex = None
        # Search direct matches
        for icon in mdi_data:
            if icon['name'] == icon_name:
                chr_hex = icon['codepoint']
                break

        # Search aliases if no direct match
        if not chr_hex:
            for icon in mdi_data:
                if 'aliases' in icon and icon_name in icon['aliases']:
                    chr_hex = icon['codepoint']
                    break

        if not chr_hex:
            raise HomeAssistantError(f"Invalid icon name: {icon_name}")

        # Get icon properties
        def load_font():
            return ImageFont.truetype(font_file, element['size'])
        font = await self.hass.async_add_executor_job(load_font)
        anchor = element.get('anchor', "la")
        fill = self.get_index_color(
            element.get('color') or element.get('fill', "black")
        )
        stroke_width = element.get('stroke_width', 0)
        stroke_fill = self.get_index_color(element.get('stroke_fill', 'white'))

        # Draw icon
        try:
            draw.text(
                (x, y),
                chr(int(chr_hex, 16)),
                fill=fill,
                font=font,
                anchor=anchor,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill
            )
        except ValueError as e:
            raise HomeAssistantError(f"Failed to draw icon: {str(e)}")

        # Calculate vertical position using text bounds
        bbox = draw.textbbox(
            (x, y),
            chr(int(chr_hex, 16)),
            font=font,
            anchor=anchor
        )
        return bbox[3]

    async def _draw_icon_sequence(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw a sequence of icons in a specified direction."""
        self.check_required_arguments(
            element,
            ["x", "y", "icons", "size"],
            "icon_sequence"
        )

        draw = ImageDraw.Draw(img)
        draw.fontmode = "1"  # Enable high quality font rendering
        coords = CoordinateParser(img.width, img.height)

        # Get basic coordinates and properties
        x_start = coords.parse_x(element['x'])
        y_start = coords.parse_y(element['y'])
        size = element['size']
        spacing = element.get('spacing', size // 4)  # Default spacing is 1/4 of icon size
        fill = self.get_index_color(element.get('fill', "black"))
        anchor = element.get('anchor', "la")
        stroke_width = element.get('stroke_width', 0)
        stroke_fill = self.get_index_color(element.get('stroke_fill', 'white'))
        direction = element.get('direction', 'right')  # right, down, up, left

        # Load MDI font and metadata
        font_file = os.path.join(os.path.dirname(__file__), 'materialdesignicons-webfont.ttf')
        meta_file = os.path.join(os.path.dirname(__file__), "materialdesignicons-webfont_meta.json")

        try:
            def load_meta():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            mdi_data = await self.hass.async_add_executor_job(load_meta)
        except Exception as e:
            raise HomeAssistantError(f"Failed to load MDI metadata: {str(e)}")

        # Load font
        def load_font():
            return ImageFont.truetype(font_file, size)
        font = await self.hass.async_add_executor_job(load_font)

        max_y = y_start
        max_x = x_start
        current_x = x_start
        current_y = y_start

        # Draw each icon in sequence
        for icon_name in element['icons']:
            if icon_name.startswith("mdi:"):
                icon_name = icon_name[4:]

            # Find icon codepoint
            chr_hex = None
            # Search direct matches
            for icon in mdi_data:
                if icon['name'] == icon_name:
                    chr_hex = icon['codepoint']
                    break

            # Search aliases if no direct match
            if not chr_hex:
                for icon in mdi_data:
                    if 'aliases' in icon and icon_name in icon['aliases']:
                        chr_hex = icon['codepoint']
                        break

            if not chr_hex:
                _LOGGER.warning(f"Invalid icon name: {icon_name}")
                continue

            # Draw icon
            try:
                draw.text(
                    (current_x, current_y),
                    chr(int(chr_hex, 16)),
                    fill=fill,
                    font=font,
                    anchor=anchor,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_fill
                )
                # Calculate bounds for this icon
                bbox = draw.textbbox(
                    (current_x, current_y),
                    chr(int(chr_hex, 16)),
                    font=font,
                    anchor=anchor
                )
                max_y = max(max_y, bbox[3])
                max_x = max(max_x, bbox[2])

                # Move to next position based on direction
                if direction == 'right':
                    current_x += size + spacing
                elif direction == 'left':
                    current_x -= size + spacing
                elif direction == 'down':
                    current_y += size + spacing
                elif direction == 'up':
                    current_y -= size + spacing

            except ValueError as e:
                raise HomeAssistantError(f"Failed to draw icon {icon_name}: {str(e)}")

        return max(max_y, current_y)

    async def _draw_qrcode(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw QR code element."""
        self.check_required_arguments(
            element,
            ["x", "y", "data"],
            "qrcode"
        )

        coords = CoordinateParser(img.width, img.height)

        # Coordinates
        x = coords.parse_x(element['x'])
        y = coords.parse_y(element['y'])

        # Get QR code properties
        color = self.get_index_color(element.get('color', "black"))
        bgcolor = self.get_index_color(element.get('bgcolor', "white"))
        border = element.get('border', 1)
        boxsize = element.get('boxsize', 2)

        try:
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=boxsize,
                border=border,
            )

            # Add data and generate QR code
            qr.add_data(element['data'])
            qr.make(fit=True)

            # Create QR code image
            qr_img = qr.make_image(fill_color=color[:3], back_color=bgcolor[:3])  # Convert RGBA to RGB
            qr_img = qr_img.convert("RGBA")

            # Calculate position
            position = (x, y)

            # Paste QR code onto main image
            img.paste(qr_img, position, qr_img)

            # Return bottom position
            return y + qr_img.height

        except Exception as e:
            raise HomeAssistantError(f"Failed to generate QR code: {str(e)}")

    async def _draw_downloaded_image(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw downloaded or local image."""
        self.check_required_arguments(
            element,
            ["x", "y", "url", "xsize", "ysize"],
            "dlimg"
        )

        try:
            # Get image properties
            pos_x = element['x']
            pos_y = element['y']
            target_size = (element['xsize'], element['ysize'])
            rotate = element.get('rotate', 0)

            # Check if URL is an image entity
            if element['url'].startswith('image.') or element['url'].startswith('camera.'):
                # Get state of the image entity
                state = self.hass.states.get(element['url'])
                if not state:
                    raise HomeAssistantError(f"Image entity {element['url']} not found")

                # Get image URL from entity attributes
                image_url = state.attributes.get("entity_picture")
                if not image_url:
                    raise HomeAssistantError(f"No image URL found for entity {element['url']}")

                # If the URL is relative, make it absolute using HA's base URL
                if image_url.startswith("/"):
                    base_url = get_url(self.hass)
                    image_url = f"{base_url}{image_url}"

                # Update URL to the actual image URL
                element['url'] = image_url

            # Load image based on URL type
            if element['url'].startswith(('http://', 'https://')):
                # Download web image
                response = await self.hass.async_add_executor_job(
                    requests.get, element['url'])
                if response.status_code != 200:
                    raise HomeAssistantError(f"Failed to download image: HTTP {response.status_code}")
                source_img = Image.open(io.BytesIO(response.content))

            elif element['url'].startswith('data:'):
                # Handle data URI
                try:
                    header, encoded = element['url'].split(',', 1)
                    if ';base64' in header:
                        decoded = base64.b64decode(encoded)
                    else:
                        decoded = urllib.parse.unquote_to_bytes(encoded)
                    source_img = Image.open(io.BytesIO(decoded))
                except Exception as e:
                    raise HomeAssistantError(f"Invalid data URI: {str(e)}")

            else:
                # Handle local file
                if not element['url'].startswith('/'):
                    media_path = self.hass.config.path('media')
                    full_path = os.path.join(media_path, element['url'])
                else:
                    full_path = element['url']
                source_img = await self.hass.async_add_executor_job(Image.open, full_path)

            # Process image
            if rotate:
                source_img = source_img.rotate(-rotate, expand=True)

            # Resize if needed
            if source_img.size != target_size:
                source_img = source_img.resize(target_size)

            # Convert to RGBA
            source_img = source_img.convert("RGBA")

            # Create temporary image for composition
            temp_img = Image.new("RGBA", img.size)
            temp_img.paste(source_img, (pos_x, pos_y), source_img)

            # Composite images
            img_composite = Image.alpha_composite(img, temp_img)
            img.paste(img_composite, (0, 0))

            return pos_y + target_size[1]

        except Exception as e:
            raise HomeAssistantError(f"Failed to process image: {str(e)}")

    async def _draw_plot(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw plot of Home Assistant sensor data."""
        self.check_required_arguments(
            element,
            ["data"],
            "plot"
        )

        try:
            draw = ImageDraw.Draw(img)

            # Get plot dimensions and position
            x_start = element.get("x_start", 0)
            y_start = element.get("y_start", 0)
            x_end = element.get("x_end", img.width - 1 - x_start)
            y_end = element.get("y_end", img.height - 1 - y_start)
            width = x_end - x_start + 1
            height = y_end - y_start + 1

            # Get time range
            duration = timedelta(seconds=element.get("duration", 60 * 60 * 24))
            end = dt.utcnow()
            start = end - duration

            # Set up fonts
            size = element.get("size", 10)
            font_file = element.get("font", "ppb.ttf")
            font_path = os.path.join(os.path.dirname(__file__), font_file)
            font = ImageFont.truetype(font_path, size)

            # Configure legend
            ylegend = element.get("ylegend", {})
            ylegend_width = ylegend.get("width", -1) if ylegend else 0
            if ylegend:
                ylegend_color = self.get_index_color(ylegend.get("color", "black"))
                ylegend_pos = ylegend.get("position", "left")
                if ylegend_pos not in ("left", "right", None):
                    ylegend_pos = "left"

                ylegend_font = font
                if ylegend.get("font") != font_file or ylegend.get("size") != size:
                    ylegend_path = os.path.join(os.path.dirname(__file__), ylegend.get("font", font_file))
                    ylegend_font = ImageFont.truetype(ylegend_path, ylegend.get("size", size))

            # Configure axis
            yaxis = element.get("yaxis", {})
            if yaxis:
                yaxis_width = yaxis.get("width", 1)
                yaxis_color = self.get_index_color(yaxis.get("color", "black"))
                yaxis_tick_width = yaxis.get("tick_width", 2)
                yaxis_tick_every = float(yaxis.get("tick_every", 1))
                yaxis_grid = yaxis.get("grid", 5)
                yaxis_grid_color = self.get_index_color(yaxis.get("grid_color", "black"))

            # Get min/max values
            min_v = element.get("low")
            max_v = element.get("high")

            # Fetch sensor data
            all_states = await get_instance(self.hass).async_add_executor_job(partial(get_significant_states,
                self.hass,
                start_time=start,
                entity_ids=[plot["entity"] for plot in element["data"]],
                significant_changes_only=False,
                minimal_response=True,
                no_attributes=False
            ))

            # Process data and find min/max if not specified
            raw_data = []
            for plot in element["data"]:
                if plot["entity"] not in all_states:
                    raise HomeAssistantError(f"No recorded data found for {plot['entity']}")

                states = all_states[plot["entity"]]
                state_obj = states[0]
                states[0] = {
                    "state": state_obj.state,
                    "last_changed": str(state_obj.last_changed)
                }

                # Convert states to points
                points = []
                for state in states:
                    try:
                        value = float(state["state"])
                        timestamp = datetime.fromisoformat(state["last_changed"])
                        points.append((timestamp, value))
                    except (ValueError, TypeError):
                        continue

                if not points:
                    continue

                # Update min/max
                values = [p[1] for p in points]
                if min_v is None:
                    min_v = min(values) if values else None
                else:
                    min_v = min(min_v, min(values))

                if max_v is None:
                    max_v = max(values) if values else None
                else:
                    max_v = max(max_v, max(values))

                raw_data.append(points)

            if not raw_data:
                raise HomeAssistantError("No valid data points found")

            # Adjust min/max
            max_v = math.ceil(max_v)
            min_v = math.floor(min_v)
            if max_v == min_v:
                min_v -= 1
            spread = max_v - min_v

            # Calculate legend width
            if ylegend_width == -1:
                ylegend_width = math.ceil(max(
                    draw.textlength(str(max_v), font=ylegend_font),
                    draw.textlength(str(min_v), font=ylegend_font)
                ))

            # Calculate effective diagram dimensions
            diag_x = x_start + (ylegend_width if ylegend_pos == "left" else 0)
            diag_y = y_start
            diag_width = width - ylegend_width
            diag_height = height

            # Draw debug borders if requested
            if element.get("debug", False):
                draw.rectangle(
                    (x_start, y_start, x_end, y_end),
                    fill=None,
                    outline=self.get_index_color("black"),
                    width=1
                )
                draw.rectangle(
                    (diag_x, diag_y, diag_x + diag_width - 1, diag_y + diag_height - 1),
                    fill=None,
                    outline=self.get_index_color("red"),
                    width=1
                )

            # Draw grid
            if yaxis and yaxis_grid is not None:
                grid_points = []
                curr = min_v
                while curr <= max_v:
                    curr_y = round(diag_y + (1 - ((curr - min_v) / spread)) * (diag_height - 1))
                    grid_points.extend(
                        (x, curr_y)
                        for x in range(diag_x, diag_x + diag_width, yaxis_grid)
                    )
                    curr += yaxis_tick_every
                if grid_points:
                    draw.point(grid_points, fill=yaxis_grid_color)

            # Draw data
            for plot_data, plot_config in zip(raw_data, element["data"]):
                # Convert data points to screen coordinates
                points = []
                for timestamp, value in plot_data:
                    rel_time = (timestamp - start) / duration
                    rel_value = (value - min_v) / spread
                    x = round(diag_x + rel_time * (diag_width - 1))
                    y = round(diag_y + (1 - rel_value) * (diag_height - 1))
                    points.append((x, y))

                # Draw line
                if len(points) > 1:
                    draw.line(
                        points,
                        fill=self.get_index_color(plot_config.get("color", "black")),
                        width=plot_config.get("width", 1),
                        joint=plot_config.get("joint")
                    )

            # Draw legend
            if ylegend:
                if ylegend_pos == "left":
                    draw.text(
                        (x_start, y_start),
                        str(max_v),
                        fill=ylegend_color,
                        font=ylegend_font,
                        anchor="lt"
                    )
                    draw.text(
                        (x_start, y_end),
                        str(min_v),
                        fill=ylegend_color,
                        font=ylegend_font,
                        anchor="ls"
                    )
                elif ylegend_pos == "right":
                    draw.text(
                        (x_end, y_start),
                        str(max_v),
                        fill=ylegend_color,
                        font=ylegend_font,
                        anchor="rt"
                    )
                    draw.text(
                        (x_end, y_end),
                        str(min_v),
                        fill=ylegend_color,
                        font=ylegend_font,
                        anchor="rs"
                    )

            # Draw axis
            if yaxis:
                draw.rectangle(
                    (diag_x, diag_y, diag_x + yaxis_width - 1, diag_y + diag_height - 1),
                    fill=yaxis_color
                )

                if yaxis_tick_width > 0:
                    curr = min_v
                    while curr <= max_v:
                        curr_y = round(diag_y + (1 - ((curr - min_v) / spread)) * (diag_height - 1))
                        draw.rectangle(
                            (diag_x + yaxis_width, curr_y, diag_x + yaxis_width + yaxis_tick_width - 1, curr_y),
                            fill=yaxis_color
                        )
                        curr += yaxis_tick_every

            return y_end

        except Exception as e:
            raise HomeAssistantError(f"Failed to draw plot: {str(e)}")

    async def _draw_progress_bar(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw progress bar with optional percentage text."""
        self.check_required_arguments(
            element,
            ["x_start", "x_end", "y_start", "y_end", "progress"],
            "progress_bar"
        )

        draw = ImageDraw.Draw(img)
        coords = CoordinateParser(img.width, img.height)

        x_start = coords.parse_x(element['x_start'])
        y_start = coords.parse_y(element['y_start'])
        x_end = coords.parse_x(element['x_end'])
        y_end = coords.parse_y(element['y_end'])

        progress = min(100, max(0, element['progress']))  # Clamp to 0-100
        direction = element.get('direction', 'right')
        background = self.get_index_color(element.get('background', 'white'))
        fill = self.get_index_color(element.get('fill', 'red'))
        outline = self.get_index_color(element.get('outline', 'black'))
        width = element.get('width', 1)
        show_percentage = element.get('show_percentage', False)

        # Draw background
        draw.rectangle(
            ((x_start, y_start), (x_end, y_end)),
            fill=background,
            outline=outline,
            width=width
        )

        # Calculate progress dimensions
        if direction in ['right', 'left']:
            progress_width = int((x_end - x_start) * (progress / 100))
            progress_height = y_end - y_start
        else:  # up or down
            progress_width = x_end - x_start
            progress_height = int((y_end - y_start) * (progress / 100))

        # Draw progress
        if direction == 'right':
            draw.rectangle(
                (x_start, y_start, x_start + progress_width, y_end),
                fill=fill
            )
        elif direction == 'left':
            draw.rectangle(
                (x_end - progress_width, y_start, x_end, y_end),
                fill=fill
            )
        elif direction == 'up':
            draw.rectangle(
                (x_start, y_end - progress_height, x_end, y_end),
                fill=fill
            )
        elif direction == 'down':
            draw.rectangle(
                (x_start, y_start, x_end, y_start + progress_height),
                fill=fill
            )

        # Draw outline
        draw.rectangle(
            (x_start, y_start, x_end, y_end),
            fill=None,
            outline=outline,
            width=width
        )

        # Add percentage text if enabled
        if show_percentage:
            # Calculate font size based on bar dimensions
            font_size = min(y_end - y_start - 4, x_end - x_start - 4, 20)
            font_path = os.path.join(os.path.dirname(__file__), 'ppb.ttf')
            font = ImageFont.truetype(font_path, font_size)

            percentage_text = f"{progress}%"

            # Get text dimensions
            text_bbox = draw.textbbox((0, 0), percentage_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            # Center text
            text_x = (x_start + x_end - text_width) / 2
            text_y = (y_start + y_end - text_height) / 2

            # Choose text color based on position relative to progress
            if progress > 50:
                text_color = background
            else:
                text_color = fill

            draw.text(
                (text_x, text_y),
                percentage_text,
                font=font,
                fill=text_color,
                anchor='lt'
            )

        return y_end

    async def _draw_diagram(self, img: Image, element: dict, pos_y: int) -> int:
        """Draw diagram with optional bars."""
        draw = ImageDraw.Draw(img)
        draw.fontmode = "1"

        # Get base properties
        pos_x = element['x']
        height = element['height']
        width = element.get('width', img.width)
        offset_lines = element.get('margin', 20)

        # Draw axes
        # X axis
        draw.line(
            [(pos_x + offset_lines, pos_y + height - offset_lines),
             (pos_x + width, pos_y + height - offset_lines)],
            fill=self.get_index_color('black'),
            width=1
        )
        # Y axis
        draw.line(
            [(pos_x + offset_lines, pos_y),
             (pos_x + offset_lines, pos_y + height - offset_lines)],
            fill=self.get_index_color('black'),
            width=1
        )

        if "bars" in element:
            bar_config = element["bars"]
            bar_margin = bar_config.get('margin', 10)
            bar_data = bar_config["values"].split(";")
            bar_count = len(bar_data)

            # Calculate bar width
            bar_width = math.floor(
                (width - offset_lines - ((bar_count + 1) * bar_margin)) / bar_count
            )

            # Set up font for legends
            size = bar_config.get('legend_size', 10)
            font_path = os.path.join(os.path.dirname(__file__), element.get('font', 'ppb.ttf'))
            font = ImageFont.truetype(font_path, size)
            legend_color = self.get_index_color(bar_config.get('legend_color', "black"))

            # Find maximum value for scaling
            max_val = 0
            for bar in bar_data:
                try:
                    name, value = bar.split(",", 1)
                    max_val = max(max_val, int(value))
                except (ValueError, IndexError):
                    continue

            if max_val == 0:
                return pos_y + height

            height_factor = (height - offset_lines) / max_val

            # Draw bars and legends
            for bar_pos, bar in enumerate(bar_data):
                try:
                    name, value = bar.split(",", 1)
                    value = int(value)

                    # Calculate bar position
                    x_pos = ((bar_margin + bar_width) * bar_pos) + offset_lines + pos_x

                    # Draw legend
                    draw.text(
                        (x_pos + (bar_width/2), pos_y + height - offset_lines/2),
                        str(name),
                        fill=legend_color,
                        font=font,
                        anchor="mm"
                    )

                    # Draw bar
                    bar_height = height_factor * value
                    draw.rectangle(
                        (x_pos, pos_y + height - offset_lines - bar_height,
                         x_pos + bar_width, pos_y + height - offset_lines),
                        fill=self.get_index_color(bar_config["color"])
                    )

                except (ValueError, IndexError, KeyError) as e:
                    _LOGGER.warning("Error processing bar data: %s", str(e))
                    continue

        return pos_y + height

    async def _draw_debug_grid(self, img: Image, element: dict, pos_y: int) -> int:

        draw = ImageDraw.Draw(img)
        width, height = img.size

        spacing = element.get("spacing", 20)
        line_color = self.get_index_color(element.get("line_color", "black"))
        dashed = element.get("dashed", True)
        dash_length = element.get("dash_length", 2)
        space_length = element.get("space_length", 4)

        show_labels = element.get("show_labels", True)
        label_step = element.get("label_step", spacing*2)
        label_color = self.get_index_color(element.get("label_color", "black"))
        label_font_size = element.get("label_font_size", 12)
        font_name = element.get("font", "ppb.ttf")

        # Load a font for labels
        font_path = os.path.join(os.path.dirname(__file__), font_name)
        try:
            font = ImageFont.truetype(font_path, label_font_size)
        except OSError:
            font = ImageFont.load_default()

        # Helper to draw one line as dashed or solid
        def draw_line_segment(p1, p2):
            if dashed:
                self._draw_dashed_line(
                    draw,
                    p1,
                    p2,
                    dash_length,
                    space_length,
                    fill=line_color,
                    width=1
                )
            else:
                draw.line([p1, p2], fill=line_color, width=1)

        # Horizontal lines
        for y in range(0, height, spacing):
            draw_line_segment((0, y), (width, y))

            # Labels
            if show_labels and (y % label_step == 0):
                label_text = str(y)
                # Slight offset so text isn't on the line
                draw.text((2, y + 2), label_text, fill=label_color, font=font)

        # Vertical lines
        for x in range(0, width, spacing):
            draw_line_segment((x, 0), (x, height))

            # Labels
            if show_labels and (x % label_step == 0):
                label_text = str(x)
                draw.text((x + 2, 2), label_text, fill=label_color, font=font)

        return pos_y


