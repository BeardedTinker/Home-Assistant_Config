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
    def __init__(self, type_id: int, data: dict):
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
        """Create TagType from stored dictionary."""
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
        """Get attribute value, supporting dict-like access."""
        return getattr(self, attr, default)

class TagTypesManager:
    """Manages tag type definitions fetched from GitHub."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._tag_types: Dict[int, TagType] = {}
        self._last_update: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self._storage_file = self._hass.config.path("open_epaper_link_tagtypes.json")
        _LOGGER.debug("TagTypesManager instance created")

    async def load_stored_data(self) -> None:
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
        """Save tag types to storage."""

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
        """Ensure tag types are loaded and not too old."""
        async with self._lock:
            _LOGGER.debug(f"Last update: {self._last_update}, {datetime.now()}")
            if not self._tag_types:
                await self.load_stored_data()

            elif (not self._last_update or
                  datetime.now() - self._last_update > CACHE_DURATION):
                await self._fetch_tag_types()

    async def _fetch_tag_types(self) -> None:
        """Fetch tag type definitions from GitHub."""
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
        """Validate that a tag definition has required fields."""
        required_fields = {'version', 'name', 'width', 'height'}
        return all(field in data for field in required_fields)

    def _load_fallback_types(self) -> None:
        """Load basic fallback definitions if fetching fails on first run."""
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
        """Get tag information (name, width, height) for a given hardware type."""
        await self.ensure_types_loaded()
        tag_def = self._tag_types[hw_type]
        return tag_def

    def get_hw_dimensions(self, hw_type: int) -> Tuple[int, int]:
        """Get width and height for a hardware type."""
        if hw_type not in self._tag_types:
            return 296, 128  # Safe defaults
        return self._tag_types[hw_type].width, self._tag_types[hw_type].height

    def get_hw_string(self, hw_type: int) -> str:
        """Get the display name for a hardware type."""
        if hw_type not in self._tag_types:
            return f"Unknown Type {hw_type}"
        return self._tag_types[hw_type].get('name', f'Unknown Type {hw_type}')

    def is_in_hw_map(self, hw_type: int) -> bool:
        """Check if a hardware type is known."""
        return hw_type in self._tag_types

    def get_all_types(self) -> Dict[int, TagType]:
        """Return all known tag types."""
        return self._tag_types.copy()

# Update the helper functions to be synchronous after initial load
_INSTANCE: Optional[TagTypesManager] = None

async def get_tag_types_manager(hass: HomeAssistant) -> TagTypesManager:
    """Get or create the global TagTypesManager instance."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = TagTypesManager(hass)
        await _INSTANCE.ensure_types_loaded()
    return _INSTANCE

def get_hw_dimensions(hw_type: int) -> Tuple[int, int]:
    """Get dimensions synchronously."""
    if _INSTANCE is None:
        return 296, 128  # Default dimensions
    return _INSTANCE.get_hw_dimensions(hw_type)

def get_hw_string(hw_type: int) -> str:
    """Get display name synchronously."""
    if _INSTANCE is None:
        return f"Unknown Type {hw_type}"
    return _INSTANCE.get_hw_string(hw_type)

def is_in_hw_map(hw_type: int) -> bool:
    """Check if hardware type exists synchronously."""
    if _INSTANCE is None:
        return False
    return _INSTANCE.is_in_hw_map(hw_type)