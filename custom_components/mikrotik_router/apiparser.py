"""API parser for JSON APIs."""

from datetime import datetime
from logging import getLogger

from pytz import utc
from voluptuous import Optional

from homeassistant.components.diagnostics import async_redact_data

from .const import TO_REDACT

_LOGGER = getLogger(__name__)


# ---------------------------
#   utc_from_timestamp
# ---------------------------
def utc_from_timestamp(timestamp: float) -> datetime:
    """Return a UTC time from a timestamp."""
    return utc.localize(datetime.utcfromtimestamp(timestamp))


# ---------------------------
#   from_entry
# ---------------------------
def from_entry(entry, param, default="") -> str:
    """Validate and return str value an API dict."""
    if "/" in param:
        for tmp_param in param.split("/"):
            if isinstance(entry, dict) and tmp_param in entry:
                entry = entry[tmp_param]
            else:
                return default

        ret = entry
    elif param in entry:
        ret = entry[param]
    else:
        return default

    if default != "":
        if isinstance(ret, str):
            ret = str(ret)
        elif isinstance(ret, int):
            ret = int(ret)
        elif isinstance(ret, float):
            ret = round(float(ret), 2)

    return ret[:255] if isinstance(ret, str) and len(ret) > 255 else ret


# ---------------------------
#   from_entry_bool
# ---------------------------
def from_entry_bool(entry, param, default=False, reverse=False) -> bool:
    """Validate and return a bool value from an API dict."""
    if "/" in param:
        for tmp_param in param.split("/"):
            if isinstance(entry, dict) and tmp_param in entry:
                entry = entry[tmp_param]
            else:
                return default

        ret = entry
    elif param in entry:
        ret = entry[param]
    else:
        return default

    if isinstance(ret, str):
        if ret in ("on", "On", "ON", "yes", "Yes", "YES", "up", "Up", "UP"):
            ret = True
        elif ret in ("off", "Off", "OFF", "no", "No", "NO", "down", "Down", "DOWN"):
            ret = False

    if not isinstance(ret, bool):
        ret = default

    return not ret if reverse else ret


# ---------------------------
#   parse_api
# ---------------------------
def parse_api(
    data=None,
    source=None,
    key=None,
    key_secondary=None,
    key_search=None,
    vals=None,
    val_proc=None,
    ensure_vals=None,
    only=None,
    skip=None,
) -> dict:
    """Get data from API."""
    debug = _LOGGER.getEffectiveLevel() == 10
    if type(source) == dict:
        tmp = source
        source = [tmp]

    if not source:
        if not key and not key_search:
            data = fill_defaults(data, vals)
        return data

    if debug:
        _LOGGER.debug("Processing source %s", async_redact_data(source, TO_REDACT))

    keymap = generate_keymap(data, key_search)
    for entry in source:
        if only and not matches_only(entry, only):
            continue

        if skip and can_skip(entry, skip):
            continue

        uid = None
        if key or key_search:
            uid = get_uid(entry, key, key_secondary, key_search, keymap)
            if not uid:
                continue

            if uid not in data:
                data[uid] = {}

        if debug:
            _LOGGER.debug("Processing entry %s", async_redact_data(entry, TO_REDACT))

        if vals:
            data = fill_vals(data, entry, uid, vals)

        if ensure_vals:
            data = fill_ensure_vals(data, uid, ensure_vals)

        if val_proc:
            data = fill_vals_proc(data, uid, val_proc)

    return data


# ---------------------------
#   get_uid
# ---------------------------
def get_uid(entry, key, key_secondary, key_search, keymap) -> Optional(str):
    """Get UID for data list."""
    uid = None
    if not key_search:
        key_primary_found = key in entry
        if key_primary_found and key not in entry and not entry[key]:
            return None

        if key_primary_found:
            uid = entry[key]
        elif key_secondary:
            if key_secondary not in entry:
                return None

            if not entry[key_secondary]:
                return None

            uid = entry[key_secondary]
    elif keymap and key_search in entry and entry[key_search] in keymap:
        uid = keymap[entry[key_search]]
    else:
        return None

    return uid or None


# ---------------------------
#   generate_keymap
# ---------------------------
def generate_keymap(data, key_search) -> Optional(dict):
    """Generate keymap."""
    return (
        {data[uid][key_search]: uid for uid in data if key_search in data[uid]}
        if key_search
        else None
    )


# ---------------------------
#   matches_only
# ---------------------------
def matches_only(entry, only) -> bool:
    """Return True if all variables are matched."""
    ret = False
    for val in only:
        if val["key"] in entry and entry[val["key"]] == val["value"]:
            ret = True
        else:
            ret = False
            break

    return ret


# ---------------------------
#   can_skip
# ---------------------------
def can_skip(entry, skip) -> bool:
    """Return True if at least one variable matches."""
    ret = False
    for val in skip:
        if val["name"] in entry and entry[val["name"]] == val["value"]:
            ret = True
            break

        if val["value"] == "" and val["name"] not in entry:
            ret = True
            break

    return ret


# ---------------------------
#   fill_defaults
# ---------------------------
def fill_defaults(data, vals) -> dict:
    """Fill defaults if source is not present."""
    for val in vals:
        _name = val["name"]
        _type = val["type"] if "type" in val else "str"
        _source = val["source"] if "source" in val else _name

        if _type == "str":
            _default = val["default"] if "default" in val else ""
            if "default_val" in val and val["default_val"] in val:
                _default = val[val["default_val"]]

            if _name not in data:
                data[_name] = from_entry([], _source, default=_default)

        elif _type == "bool":
            _default = val["default"] if "default" in val else False
            _reverse = val["reverse"] if "reverse" in val else False
            if _name not in data:
                data[_name] = from_entry_bool(
                    [], _source, default=_default, reverse=_reverse
                )

    return data


# ---------------------------
#   fill_vals
# ---------------------------
def fill_vals(data, entry, uid, vals) -> dict:
    """Fill all data."""
    for val in vals:
        _name = val["name"]
        _type = val["type"] if "type" in val else "str"
        _source = val["source"] if "source" in val else _name
        _convert = val["convert"] if "convert" in val else None

        if _type == "str":
            _default = val["default"] if "default" in val else ""
            if "default_val" in val and val["default_val"] in val:
                _default = val[val["default_val"]]

            if uid:
                data[uid][_name] = from_entry(entry, _source, default=_default)
            else:
                data[_name] = from_entry(entry, _source, default=_default)

        elif _type == "bool":
            _default = val["default"] if "default" in val else False
            _reverse = val["reverse"] if "reverse" in val else False

            if uid:
                data[uid][_name] = from_entry_bool(
                    entry, _source, default=_default, reverse=_reverse
                )
            else:
                data[_name] = from_entry_bool(
                    entry, _source, default=_default, reverse=_reverse
                )

        if _convert == "utc_from_timestamp":
            if uid:
                if isinstance(data[uid][_name], int) and data[uid][_name] > 0:
                    if data[uid][_name] > 100000000000:
                        data[uid][_name] = data[uid][_name] / 1000

                    data[uid][_name] = utc_from_timestamp(data[uid][_name])
            elif isinstance(data[_name], int) and data[_name] > 0:
                if data[_name] > 100000000000:
                    data[_name] = data[_name] / 1000

                data[_name] = utc_from_timestamp(data[_name])

    return data


# ---------------------------
#   fill_ensure_vals
# ---------------------------
def fill_ensure_vals(data, uid, ensure_vals) -> dict:
    """Add required keys which are not available in data."""
    for val in ensure_vals:
        if uid:
            if val["name"] not in data[uid]:
                _default = val["default"] if "default" in val else ""
                data[uid][val["name"]] = _default

        elif val["name"] not in data:
            _default = val["default"] if "default" in val else ""
            data[val["name"]] = _default

    return data


# ---------------------------
#   fill_vals_proc
# ---------------------------
def fill_vals_proc(data, uid, vals_proc) -> dict:
    """Add custom keys."""
    _data = data[uid] if uid else data
    for val_sub in vals_proc:
        _name = None
        _action = None
        _value = None
        for val in val_sub:
            if "name" in val:
                _name = val["name"]
                continue

            if "action" in val:
                _action = val["action"]
                continue

            if not _name and not _action:
                break

            if _action == "combine":
                if "key" in val:
                    tmp = _data[val["key"]] if val["key"] in _data else "unknown"
                    _value = f"{_value}{tmp}" if _value else tmp

                if "text" in val:
                    tmp = val["text"]
                    _value = f"{_value}{tmp}" if _value else tmp

        if _name and _value:
            if uid:
                data[uid][_name] = _value
            else:
                data[_name] = _value

    return data
