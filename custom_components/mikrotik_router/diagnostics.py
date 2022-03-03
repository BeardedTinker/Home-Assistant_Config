"""Diagnostics support for Mikrotik Router."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    "ip-address",
    "client-ip-address",
    "address",
    "active-address",
    "mac-address",
    "active-mac-address",
    "orig-mac-address",
    "port-mac-address",
    "client-mac-address",
    "client-id",
    "active-client-id",
    "eeprom",
    "sfp-vendor-serial",
    "gateway",
    "dns-server",
    "wins-server",
    "ntp-server",
    "caps-manager",
    "serial-number",
    "source",
    "from-addresses",
    "to-addresses",
    "src-address",
    "dst-address",
    "username",
    "password",
    "caller-id",
    "target",
    "ssid",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    controller = hass.data[DOMAIN][config_entry.entry_id]
    diag: dict[str, Any] = {}
    diag["entry"]: dict[str, Any] = {}

    diag["entry"]["data"] = async_redact_data(config_entry.data, TO_REDACT)
    diag["entry"]["options"] = async_redact_data(config_entry.options, TO_REDACT)
    diag["data"] = async_redact_data(controller.data, TO_REDACT)

    return diag
