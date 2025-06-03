"""Button platform for Moonraker integration."""

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .const import DOMAIN, METHODS
from .entity import BaseMoonrakerEntity


@dataclass
class MoonrakerButtonDescription(ButtonEntityDescription):
    """Class describing Mookraker button entities."""

    press_fn: Callable | None = None
    button_name: str | None = None
    icon: str | None = None
    unit: str | None = None
    device_class: str | None = None


BUTTONS: tuple[MoonrakerButtonDescription, ...] = [
    MoonrakerButtonDescription(
        key="emergency_stop",
        name="Emergency Stop",
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.PRINTER_EMERGENCY_STOP
        ),
        icon="mdi:alert-octagon-outline",
    ),
    MoonrakerButtonDescription(
        key="pause_print",
        name="Pause Print",
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.PRINTER_PRINT_PAUSE
        ),
        icon="mdi:pause",
    ),
    MoonrakerButtonDescription(
        key="resume_print",
        name="Resume Print",
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.PRINTER_PRINT_RESUME
        ),
        icon="mdi:play",
    ),
    MoonrakerButtonDescription(
        key="cancel_print",
        name="Cancel Print",
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.PRINTER_PRINT_CANCEL
        ),
        icon="mdi:stop",
    ),
    MoonrakerButtonDescription(
        key="server_restart",
        name="Server Restart",
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.SERVER_RESTART
        ),
        icon="mdi:restart",
    ),
    MoonrakerButtonDescription(
        key="host_restart",
        name="Host Restart",
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.HOST_RESTART
        ),
        icon="mdi:restart",
    ),
    MoonrakerButtonDescription(
        key="firmware_restart",
        name="Firmware Restart",
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.PRINTER_FIRMWARE_RESTART
        ),
        icon="mdi:restart",
    ),
    MoonrakerButtonDescription(
        key="host_shutdown",
        name="Host Shutdown",
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.HOST_SHUTDOWN
        ),
        icon="mdi:restart",
    ),
    MoonrakerButtonDescription(
        key="machine_update_refresh",
        name="Machine Update Refresh",
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.MACHINE_UPDATE_REFRESH
        ),
        icon="mdi:refresh",
    ),
    MoonrakerButtonDescription(
        key="reset_totals",
        name="Reset Totals",
        entity_registry_enabled_default=False,
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.SERVER_HISTORY_RESET_TOTALS
        ),
        icon="mdi:history",
    ),
    MoonrakerButtonDescription(
        key="start_print_from_queue",
        name="Start Print from Queue",
        press_fn=lambda button: button.coordinator.async_send_data(
            METHODS.SERVER_JOB_QUEUE_START
        ),
        icon="mdi:playlist-play",
    ),
]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await async_setup_basic_buttons(coordinator, entry, async_add_entities)
    await async_setup_macros(coordinator, entry, async_add_entities)


async def async_setup_basic_buttons(coordinator, entry, async_add_entities):
    """Set optional button platform."""
    async_add_entities([MoonrakerButton(coordinator, entry, desc) for desc in BUTTONS])


async def async_setup_macros(coordinator, entry, async_add_entities):
    """Set optional button platform."""
    cmds = await coordinator.async_fetch_data(METHODS.PRINTER_GCODE_HELP)

    macros = []
    for cmd, desc in cmds.items():
        enable_by_default = False
        if desc == "G-Code macro":
            enable_by_default = True

        macros.append(
            MoonrakerButtonDescription(
                key=cmd,
                name="Macro " + cmd.lower().replace("_", " ").title(),
                press_fn=lambda button: button.coordinator.async_send_data(
                    METHODS.PRINTER_GCODE_SCRIPT, {"script": button.invoke_name}
                ),
                icon="mdi:play",
                entity_registry_enabled_default=enable_by_default,
            )
        )

    async_add_entities([MoonrakerButton(coordinator, entry, desc) for desc in macros])


class MoonrakerButton(BaseMoonrakerEntity, ButtonEntity):
    """MoonrakerSensor Sensor class."""

    def __init__(self, coordinator, entry, description):
        """Intit."""
        super().__init__(coordinator, entry)
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = True
        self.entity_description = description
        self._attr_icon = description.icon
        self.invoke_name = description.key
        self.press_fn = description.press_fn

    async def async_press(self) -> None:
        """Press the button."""
        await self.press_fn(self)
