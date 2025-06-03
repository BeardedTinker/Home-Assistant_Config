from __future__ import annotations

import os.path

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Tuple, Optional, Any, cast
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/repos/OpenEPaperLink/OpenEPaperLink/contents/resources/tagtypes"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/OpenEPaperLink/OpenEPaperLink/master/resources/tagtypes"
CACHE_DURATION = timedelta(hours=48)  # Cache tag definitions for 48 hours
STORAGE_VERSION = 1


class TagType:
    """Represents a specific tag hardware type and its capabilities.

    Encapsulates all the hardware-specific properties of a tag model, including:

    - Display dimensions and color capabilities
    - Buffer format and rotation settings
    - LUT (Look-Up Table) configuration
    - Content type compatibility

    This information is used for proper image generation and rendering
    to ensure content displays correctly on different tag models.

    Attributes:
        type_id: Numeric identifier for the tag type
        version: Format version of the tag type definition
        name: Human-readable name of the tag model
        width: Display width in pixels
        height: Display height in pixels
        rotatebuffer: Buffer rotation setting (0=none, 1=90°, 2=180°, 3=270°)
        bpp: Bits per pixel (color depth)
        color_table: Mapping of color names to RGB values
        short_lut: Short LUT configuration
        options: Additional tag options
        content_ids: Compatible content IDs
        template: Template configuration
        use_template: Template usage settings
        zlib_compression: Compression settings
    """

    def __init__(self, type_id: int, data: dict):
        """Initialize a tag type from type ID and properties.

        Creates a TagType instance by mapping properties from the
        provided data dictionary to class attributes, with defaults
        for missing properties.

        Args:
            type_id: Numeric identifier for this tag type
            data: Dictionary containing tag properties from GitHub or storage
        """
        self.type_id = type_id
        self.version = data.get('version', 1)
        self.name = data.get('name', f"Unknown Type {type_id}")
        self.width = data.get('width', 296)
        self.height = data.get('height', 128)
        self.rotatebuffer = data.get('rotatebuffer', 0)
        self.bpp = data.get('bpp', 2)
        self.color_table = data.get('colortable', {
            'white': [255, 255, 255],
            'black': [0, 0, 0],
            'red': [255, 0, 0],
        })
        self.short_lut = data.get('shortlut', 2)
        self.options = data.get('options', [])
        self.content_ids = data.get('contentids', [])
        self.template = data.get('template', {})
        self.use_template = data.get('usetemplate', None)
        self.zlib_compression = data.get('zlib_compression', None)
        self._raw_data = data

    def to_dict(self) -> dict:
        """Convert TagType instance to a serializable dictionary.

        Creates a dictionary representation of the tag type suitable for
        storage. This is used when saving to persistent storage.

        Returns:
            dict: Dictionary containing all tag type properties
        """
        return {
            'version': self.version,
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'rotatebuffer': self.rotatebuffer,
            'bpp': self.bpp,
            'colortable': self.color_table,
            'shortlut': self.short_lut,
            'options': list(self.options),
            'contentids': list(self.content_ids),
            'template': self.template,
            'usetemplate': self.use_template,
            'zlib_compression': self.zlib_compression,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TagType:
        """Create TagType from stored dictionary.

        Factory method to reconstruct a TagType instance from a previously
        serialized dictionary when loaded from persistent storage.

        Args:
            data: Dictionary containing serialized tag type properties

        Returns:
            TagType: Reconstructed tag type instance
        """
        raw_data = {
            'version': data.get('version', 1),
            'name': data.get('name'),
            'width': data.get('width'),
            'height': data.get('height'),
            'rotatebuffer': data.get('rotatebuffer'),
            'bpp': data.get('bpp'),
            'shortlut': data.get('short_lut'),
            'colortable': data.get('colortable'),
            'options': data.get('options', []),
            'contentids': data.get('content_ids', []),
            'template': data.get('template', {}),
            'zlib_compression': data.get('zlib_compression', None),
        }
        return cls(data.get('type_id'), raw_data)

    def get(self, attr: str, default: Any = None) -> Any:
        """Get attribute value, supporting dict-like access.

        Provides dictionary-style access to tag type attributes,
        with a default value if the attribute doesn't exist.

        Args:
            attr: Name of the attribute to retrieve
            default: Value to return if attribute doesn't exist

        Returns:
            Any: The attribute value or default if not found
        """
        return getattr(self, attr, default)


class TagTypesManager:
    """Manages tag type definitions fetched from GitHub.

    Handles loading, caching, and refreshing tag type definitions from
    the OpenEPaperLink GitHub repository. Provides local storage to
    avoid frequent network requests and fallback definitions for
    when GitHub is unreachable.

    The manager is implemented as a quasi-singleton through the
    get_tag_types_manager function to ensure consistent state
    across the integration.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the tag types manager.

        Sets up the manager with empty state and configuration paths
        derived from the Home Assistant instance.

        Args:
            hass: Home Assistant instance for storage access
        """
        self._hass = hass
        self._tag_types: Dict[int, TagType] = {}
        self._last_update: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self._storage_file = self._hass.config.path("open_epaper_link_tagtypes.json")
        _LOGGER.debug("TagTypesManager instance created")

    async def load_stored_data(self) -> None:
        """Load stored tag type definitions from disk.

        Attempts to load previously cached tag type definitions from the
        local storage file. If valid data is found, it's used to populate
        the manager's state. Otherwise, a fresh fetch from GitHub is initiated.

        This helps reduce network requests and provides offline operation capability.
        """
        try:
            _LOGGER.debug("Attempting to load stored tag types from %s", self._storage_file)

            def load_json():
                """Load JSON file if it exists."""
                if os.path.exists(self._storage_file):
                    with open(self._storage_file, 'r', encoding='utf-8') as fp:
                        return json.load(fp)
                return None

            stored_data = await self._hass.async_add_executor_job(load_json)

            if stored_data and stored_data.get('version') == STORAGE_VERSION:
                _LOGGER.info("Found valid stored tag types data")
                self._last_update = datetime.fromisoformat(stored_data.get('last_update'))

                # Convert stored data back to TagType objects
                self._tag_types = {}
                for type_id_str, type_data in stored_data.get('tag_types', {}).items():
                    try:
                        type_id = int(type_id_str)
                        self._tag_types[type_id] = TagType.from_dict(type_data)
                        _LOGGER.debug("Loaded tag type %d: %s",
                                      type_id, self._tag_types[type_id].name)
                    except Exception as e:
                        _LOGGER.error("Error loading tag type %s: %s", type_id_str, str(e))

                _LOGGER.info("Loaded %d tag types from storage", len(self._tag_types))
                return
            else:
                _LOGGER.warning("Stored data invalid or wrong version, will fetch from GitHub")

        except Exception as e:
            _LOGGER.error("Error loading stored tag types: %s", str(e), exc_info=True)

        # If we get here, either no stored data or invalid data
        await self._fetch_tag_types()

    async def save_to_storage(self) -> None:
        """Save tag types to persistent storage.

        Serializes current tag type definitions to JSON and saves them
        to the local storage file. Uses atomic writes to prevent data
        corruption if interrupted.

        The storage format includes a version identifier and timestamp
        to facilitate future compatibility and freshness checking.
        """

        try:
            _LOGGER.debug("Saving tag types to storage")
            data = {
                'version': STORAGE_VERSION,
                'last_update': self._last_update.isoformat(),
                'tag_types': {
                    str(type_id): tag_type.to_dict()
                    for type_id, tag_type in self._tag_types.items()
                }
            }

            def write_json():
                temp_file = f"{self._storage_file}.temp"
                try:
                    with open(temp_file, 'w', encoding='utf-8') as file:
                        json.dump(data, file, default=str, indent=2)
                    os.replace(temp_file, self._storage_file)
                except Exception as e:
                    _LOGGER.error(f"Error writing tag types to storage: {str(e)}")
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    raise e

            await self._hass.async_add_executor_job(write_json)
            _LOGGER.debug("Tag types saved to storage")
        except Exception as e:
            _LOGGER.error(f"Error saving tag types to storage: {str(e)}")

    async def ensure_types_loaded(self) -> None:
        """Ensure tag types are loaded and not too old.

        Checks if tag types are already loaded and sufficiently recent.
        If not loaded or older than CACHE_DURATION, initiates a refresh from GitHub.

        This is the primary method that should be called before accessing
        tag type information to ensure data availability.
        """
        async with self._lock:
            _LOGGER.debug(f"Last update: {self._last_update}, {datetime.now()}")
            if not self._tag_types:
                await self.load_stored_data()

            elif (not self._last_update or
                  datetime.now() - self._last_update > CACHE_DURATION):
                await self._fetch_tag_types()

    async def _fetch_tag_types(self) -> None:
        """Fetch tag type definitions from GitHub.

        Retrieves tag type definitions from the OpenEPaperLink GitHub repository:

        1. Queries the GitHub API to list available definition files
        2. Downloads each file and parses as JSON
        3. Validates the definition contains required fields
        4. Creates TagType instances from valid definitions

        If fetching fails and no existing definitions are available,
        falls back to built-in basic definitions.
        """
        try:
            async with aiohttp.ClientSession() as session:
                # First get the directory listing from GitHub API
                headers = {"Accept": "application/vnd.github.v3+json"}
                async with session.get(GITHUB_API_URL, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"GitHub API returned status {response.status}")

                    directory_contents = await response.json()

                    # Filter for .json files and extract type IDs
                    type_files = []
                    for item in directory_contents:
                        if item["name"].endswith(".json"):
                            # Try to extract type ID from filename
                            try:
                                base_name = item["name"][:-5]  # Remove .json extension
                                try:
                                    type_id = int(base_name, 16)
                                    _LOGGER.debug(f"Parsed hex type ID {base_name} -> {type_id}")
                                    type_files.append((type_id, item["download_url"]))
                                    continue
                                except ValueError:
                                    pass

                                # If not hex, try decimal
                                try:
                                    type_id = int(base_name)
                                    _LOGGER.debug(f"Parsed decimal type ID {base_name} -> {type_id}")
                                    type_files.append((type_id, item["download_url"]))
                                    continue
                                except ValueError:
                                    pass
                                _LOGGER.warning(f"Could not parse type ID from filename: {item['name']}")

                            except Exception as e:
                                _LOGGER.warning(f"Error processing filename {item['name']}: {str(e)}")

                # Now fetch all found definitions
                new_types = {}
                for hw_type, url in type_files:
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                text_content = await response.text()
                                try:
                                    data = json.loads(text_content)
                                    if self._validate_tag_definition(data):
                                        new_types[hw_type] = TagType(hw_type, data)
                                        _LOGGER.debug(f"Loaded tag type {hw_type}: {data['name']}")
                                except json.JSONDecodeError:
                                    _LOGGER.error(f"Invalid JSON in tag type {hw_type}")
                    except Exception as e:
                        _LOGGER.error(f"Error loading tag type {hw_type}: {str(e)}")

                if new_types:
                    self._tag_types = new_types
                    self._last_update = datetime.now()
                    _LOGGER.info(f"Successfully loaded {len(new_types)} tag definitions")
                    await self.save_to_storage()
                else:
                    _LOGGER.error("No valid tag definitions found")

        except Exception as e:
            _LOGGER.error(f"Error fetching tag types: {str(e)}")
            if not self._tag_types:
                # Load built-in fallback for first-time failures
                self._load_fallback_types()
                await self.save_to_storage()

    def _validate_tag_definition(self, data: Dict) -> bool:
        """Validate that a tag definition has required fields.

        Checks if the tag definition dictionary contains all required fields
        to be considered valid. A valid definition must include:

        - version: Tag type format version
        - name: Human-readable model name
        - width: Display width in pixels
        - height: Display height in pixels

        Args:
            data: Dictionary containing tag type definition

        Returns:
            bool: True if the definition is valid, False otherwise
        """
        required_fields = {'version', 'name', 'width', 'height'}
        return all(field in data for field in required_fields)

    def _load_fallback_types(self) -> None:
        """Load basic fallback definitions if fetching fails on first run.

        Populates the manager with a minimal set of built-in tag type
        definitions to ensure basic functionality when GitHub is unreachable.

        This provides support for common tag models with basic dimensions,
        though without detailed configuration options.

        The fallback types include:

        - Common M2 tag sizes (1.54", 2.9", 4.2")
        - AP display types
        - LILYGO TPANEL
        - Segmented tag type
        """
        self._tag_types = {
            0: {"name": "M2 1.54\"", "width": 152, "height": 152},
            1: {"name": "M2 2.9\"", "width": 296, "height": 128},
            2: {"name": "M2 4.2\"", "width": 400, "height": 300},
            224: {"name": "AP display", "width": 320, "height": 170},
            225: {"name": "AP display", "width": 160, "height": 80},
            226: {"name": "LILYGO TPANEL", "width": 480, "height": 480},
            240: {"name": "Segmented", "width": 0, "height": 0}
        }
        _LOGGER.warning("Loaded fallback tag definitions")

    async def get_tag_info(self, hw_type: int) -> TagType:
        """Get tag information for a specific hardware type.

        Retrieves the TagType instance for the specified hardware type,
        ensuring type definitions are loaded first if needed.

        This method should be used to get tag information
        when processing tag data from the AP.

        Args:
            hw_type: Hardware type ID number

        Returns:
            TagType: Tag type definition object

        Raises:
            KeyError: If the hardware type is unknown
        """
        await self.ensure_types_loaded()
        tag_def = self._tag_types[hw_type]
        return tag_def

    def get_hw_dimensions(self, hw_type: int) -> Tuple[int, int]:
        """Get width and height for a hardware type.

        Returns the display dimensions for the specified tag type.
        If the type is unknown, returns safe default values.

        Args:
            hw_type: Hardware type ID number

        Returns:
            Tuple[int, int]: Width and height in pixels
        """
        if hw_type not in self._tag_types:
            return 296, 128  # Safe defaults
        return self._tag_types[hw_type].width, self._tag_types[hw_type].height

    def get_hw_string(self, hw_type: int) -> str:
        """Get the display name for a hardware type.

        Returns a human-readable name for the tag hardware type.

        Args:
            hw_type: Hardware type ID number

        Returns:
            str: Human-readable name or "Unknown Type {hw_type}" if not recognized
        """
        if hw_type not in self._tag_types:
            return f"Unknown Type {hw_type}"
        return self._tag_types[hw_type].get('name', f'Unknown Type {hw_type}')

    def is_in_hw_map(self, hw_type: int) -> bool:
        """Check if a hardware type is known to the manager.

        Determines whether the specified hardware type ID has a
        definition available in the manager.

        Args:
            hw_type: Hardware type ID to check

        Returns:
            bool: True if the hardware type is known, False otherwise
        """
        return hw_type in self._tag_types

    def get_all_types(self) -> Dict[int, TagType]:
        """Return all known tag types.

        Provides a copy of the complete type map.
        This is useful for debugging or for UIs that
        need to display all available tag types.

        Returns:
            Dict[int, TagType]: Dictionary mapping type IDs to TagType instances
        """
        return self._tag_types.copy()


# Update the helper functions to be synchronous after initial load
_INSTANCE: Optional[TagTypesManager] = None


async def get_tag_types_manager(hass: HomeAssistant) -> TagTypesManager:
    """Get or create the global TagTypesManager instance.

    Implements a singleton pattern to ensure only one tag types manager
    exists per Home Assistant instance. If the manager doesn't exist yet,
    creates and initializes it.

    Args:
        hass: Home Assistant instance

    Returns:
        TagTypesManager: The shared manager instance
    """
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = TagTypesManager(hass)
        await _INSTANCE.ensure_types_loaded()
    return _INSTANCE


def get_hw_dimensions(hw_type: int) -> Tuple[int, int]:
    """Get dimensions synchronously from global instance.

    Synchronous wrapper around the TagTypesManager.get_hw_dimensions method
    that uses the global manager instance. Returns default dimensions
    if the manager isn't initialized yet.

    Args:
        hw_type: Hardware type ID number

    Returns:
        Tuple[int, int]: Width and height in pixels (defaults to 296x128)
    """
    if _INSTANCE is None:
        return 296, 128  # Default dimensions
    return _INSTANCE.get_hw_dimensions(hw_type)


def get_hw_string(hw_type: int) -> str:
    """Get display name synchronously from global instance.

    Synchronous wrapper around the TagTypesManager.get_hw_string method
    that uses the global manager instance. Returns a default string
    if the manager isn't initialized yet.

    Args:
        hw_type: Hardware type ID number

    Returns:
        str: Human-readable name or "Unknown Type {hw_type}" if not recognized
    """
    if _INSTANCE is None:
        return f"Unknown Type {hw_type}"
    return _INSTANCE.get_hw_string(hw_type)


def is_in_hw_map(hw_type: int) -> bool:
    """Get display name synchronously from global instance.

    Synchronous wrapper around the TagTypesManager.is_in_hw_map method
    that uses the global manager instance. Returns `false`
    if the manager isn't initialized yet.

    Args:
        hw_type: Hardware type ID number

    Returns:
        bool: True if the hardware type is known, False otherwise
    """
    if _INSTANCE is None:
        return False
    return _INSTANCE.is_in_hw_map(hw_type)
