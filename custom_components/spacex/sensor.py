"""Definition and setup of the SpaceX Binary Sensors for Home Assistant."""

import datetime
import logging

from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.const import LENGTH_KILOMETERS, SPEED_KILOMETERS_PER_HOUR
from homeassistant.helpers.entity import Entity

from .const import COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the sensor platforms."""

    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    sensors = []

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Next Launch Mission",
            "spacex_next_launch_mission",
            "mdi:information-outline",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Next Launch Day",
            "spacex_next_launch_day",
            "mdi:calendar",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Next Launch Time",
            "spacex_next_launch_time",
            "mdi:clock-outline",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Next Launch Site",
            "spacex_next_launch_site",
            "mdi:map-marker",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Next Launch Rocket",
            "spacex_next_launch_rocket",
            "mdi:rocket",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Next Launch Payload",
            "spacex_next_launch_payload",
            "mdi:package",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Latest Launch Mission",
            "spacex_latest_launch_mission",
            "mdi:information-outline",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Latest Launch Day",
            "spacex_latest_launch_day",
            "mdi:calendar",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Latest Launch Time",
            "spacex_latest_launch_time",
            "mdi:clock-outline",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Latest Launch Site",
            "spacex_latest_launch_site",
            "mdi:map-marker",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Latest Launch Rocket",
            "spacex_latest_launch_rocket",
            "mdi:rocket",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Latest Launch Payload",
            "spacex_latest_launch_payload",
            "mdi:package",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Starman Speed",
            "spacex_starman_speed",
            "mdi:account-star",
            "spacexstarman",
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Starman Distance",
            "spacex_starman_distance",
            "mdi:map-marker-distance",
            "spacexstarman",
        )
    )

    async_add_entities(sensors, update_before_add=True)


class SpaceXSensor(Entity):
    """Defines a SpaceX Binary sensor."""

    def __init__(self, coordinator, name, entity_id, icon, device_identifier):
        """Initialize Entities."""

        self._name = name
        self.entity_id = ENTITY_ID_FORMAT.format(entity_id)
        self._state = None
        self._icon = icon
        self._kind = entity_id
        self._device_identifier = device_identifier
        self.coordinator = coordinator
        self._unit_of_measure = None
        self.attrs = {}

    @property
    def should_poll(self):
        """Return the polling requirement of an entity."""
        return True

    @property
    def unique_id(self):
        """Return the unique Home Assistant friendly identifier for this entity."""
        return self.entity_id

    @property
    def name(self):
        """Return the friendly name of this entity."""
        return self._name

    @property
    def icon(self):
        """Return the icon for this entity."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement for this entity."""
        return self._unit_of_measure

    @property
    def device_state_attributes(self):
        """Return the attributes."""
        return self.attrs

    @property
    def state(self):
        """Return the state."""
        return self._state

    async def async_update(self):
        """Update SpaceX Binary Sensor Entity."""
        await self.coordinator.async_request_refresh()
        _LOGGER.debug("Updating state of the sensors.")
        coordinator_data = self.coordinator.data
        starman_data = coordinator_data[0]
        launch_data = coordinator_data[1]
        latest_launch_data = coordinator_data[2]

        self.attrs["last_updated"] = launch_data.get("last_date_update")

        if self._kind == "spacex_next_launch_mission":
            self._state = launch_data.get("mission_name")
            self.attrs["mission_patch"] = launch_data["links"].get("mission_patch")
            if launch_data.get("details") is not None:
                self.attrs["details"] = launch_data.get("details")[0:255]
            self.attrs["video_link"] = launch_data["links"].get("video_link")

        elif self._kind == "spacex_next_launch_day":
            self._state = datetime.datetime.fromtimestamp(
                launch_data.get("launch_date_unix")
            ).strftime("%d-%b-%Y")
            self.attrs["launch_date_unix"] = launch_data.get("launch_date_unix")
            self.attrs["launch_date_utc"] = launch_data.get("launch_date_utc")

        elif self._kind == "spacex_next_launch_time":
            self._state = datetime.datetime.fromtimestamp(
                launch_data.get("launch_date_unix")
            ).strftime("%I:%M %p")

        elif self._kind == "spacex_next_launch_site":
            self._state = launch_data["launch_site"].get("site_name_long")
            self.attrs["short_name"] = launch_data["launch_site"].get("site_name")

        elif self._kind == "spacex_next_launch_rocket":
            self._state = launch_data["rocket"].get("rocket_name")
            core_counter = 1
            for this_core in launch_data["rocket"]["first_stage"].get("cores"):
                self.attrs["core_" + str(core_counter) + "_serial"] = this_core.get(
                    "core_serial"
                )
                self.attrs["core_" + str(core_counter) + "_flight"] = this_core.get(
                    "flight"
                )
                self.attrs["core_" + str(core_counter) + "_block"] = this_core.get(
                    "block"
                )
                self.attrs[
                    "core_" + str(core_counter) + "_landing_intent"
                ] = this_core.get("landing_intent")
                self.attrs["core_" + str(core_counter) + "_lz"] = this_core.get(
                    "landing_vehicle"
                )
                core_counter = core_counter + 1
            self.attrs["fairings_reused"] = launch_data["rocket"]["fairings"].get(
                "reused"
            )

        elif self._kind == "spacex_next_launch_payload":
            self._state = launch_data["rocket"]["second_stage"]["payloads"][0].get(
                "payload_id"
            )
            self.attrs["nationality"] = launch_data["rocket"]["second_stage"][
                "payloads"
            ][0].get("nationality")
            self.attrs["manufacturer"] = launch_data["rocket"]["second_stage"][
                "payloads"
            ][0].get("manufacturer")
            self.attrs["payload_type"] = launch_data["rocket"]["second_stage"][
                "payloads"
            ][0].get("payload_type")
            self.attrs["payload_mass"] = (
                str(
                    launch_data["rocket"]["second_stage"]["payloads"][0].get(
                        "payload_mass_kg"
                    )
                )
                + " kg"
            )
            self.attrs["payload_mass_us"] = (
                str(
                    launch_data["rocket"]["second_stage"]["payloads"][0].get(
                        "payload_mass_lbs"
                    )
                )
                + " lbs"
            )
            self.attrs["orbit"] = launch_data["rocket"]["second_stage"]["payloads"][
                0
            ].get("orbit")

        elif self._kind == "spacex_latest_launch_mission":
            self._state = latest_launch_data.get("mission_name")
            self.attrs["mission_patch"] = latest_launch_data["links"].get("mission_patch")
            if latest_launch_data.get("details") is not None:
                self.attrs["details"] = latest_launch_data.get("details")[0:255]
            self.attrs["video_link"] = latest_launch_data["links"].get("video_link")

        elif self._kind == "spacex_latest_launch_day":
            self._state = datetime.datetime.fromtimestamp(
                latest_launch_data.get("launch_date_unix")
            ).strftime("%d-%b-%Y")
            self.attrs["launch_date_unix"] = latest_launch_data.get("launch_date_unix")
            self.attrs["launch_date_utc"] = latest_launch_data.get("launch_date_utc")

        elif self._kind == "spacex_latest_launch_time":
            self._state = datetime.datetime.fromtimestamp(
                latest_launch_data.get("launch_date_unix")
            ).strftime("%I:%M %p")

        elif self._kind == "spacex_latest_launch_site":
            self._state = latest_launch_data["launch_site"].get("site_name_long")
            self.attrs["short_name"] = latest_launch_data["launch_site"].get("site_name")

        elif self._kind == "spacex_latest_launch_rocket":
            self._state = latest_launch_data["rocket"].get("rocket_name")
            core_counter = 1
            for this_core in latest_launch_data["rocket"]["first_stage"].get("cores"):
                self.attrs["core_" + str(core_counter) + "_serial"] = this_core.get(
                    "core_serial"
                )
                self.attrs["core_" + str(core_counter) + "_flight"] = this_core.get(
                    "flight"
                )
                self.attrs["core_" + str(core_counter) + "_block"] = this_core.get(
                    "block"
                )
                self.attrs[
                    "core_" + str(core_counter) + "_landing_intent"
                ] = this_core.get("landing_intent")
                self.attrs["core_" + str(core_counter) + "_lz"] = this_core.get(
                    "landing_vehicle"
                )
                core_counter = core_counter + 1
            self.attrs["fairings_reused"] = latest_launch_data["rocket"]["fairings"].get(
                "reused"
            )

        elif self._kind == "spacex_latest_launch_payload":
            self._state = latest_launch_data["rocket"]["second_stage"]["payloads"][0].get(
                "payload_id"
            )
            self.attrs["nationality"] = latest_launch_data["rocket"]["second_stage"][
                "payloads"
            ][0].get("nationality")
            self.attrs["manufacturer"] = latest_launch_data["rocket"]["second_stage"][
                "payloads"
            ][0].get("manufacturer")
            self.attrs["payload_type"] = latest_launch_data["rocket"]["second_stage"][
                "payloads"
            ][0].get("payload_type")
            self.attrs["payload_mass"] = (
                str(
                    latest_launch_data["rocket"]["second_stage"]["payloads"][0].get(
                        "payload_mass_kg"
                    )
                )
                + " kg"
            )
            self.attrs["payload_mass_us"] = (
                str(
                    latest_launch_data["rocket"]["second_stage"]["payloads"][0].get(
                        "payload_mass_lbs"
                    )
                )
                + " lbs"
            )
            self.attrs["orbit"] = latest_launch_data["rocket"]["second_stage"]["payloads"][
                0
            ].get("orbit")

        elif self._kind == "spacex_starman_speed":
            self._state = int(starman_data["speed_kph"])
            self._unit_of_measure = SPEED_KILOMETERS_PER_HOUR

        elif self._kind == "spacex_starman_distance":
            self._state = int(starman_data["earth_distance_km"])
            self._unit_of_measure = LENGTH_KILOMETERS

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
