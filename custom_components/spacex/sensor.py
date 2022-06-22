"""Definition and setup of the SpaceX Binary Sensors for Home Assistant."""

import logging
import time
import datetime

from homeassistant.util.dt import as_local, utc_from_timestamp
from homeassistant.components.sensor import ENTITY_ID_FORMAT, DEVICE_CLASS_TIMESTAMP
from homeassistant.const import LENGTH_KILOMETERS, SPEED_KILOMETERS_PER_HOUR, ATTR_NAME
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from . import SpaceXUpdateCoordinator

from .const import ATTR_IDENTIFIERS, ATTR_MANUFACTURER, ATTR_MODEL, DOMAIN, COORDINATOR

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
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
            "Next Launch Countdown",
            "spacex_next_launch_countdown",
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
            "Next Confirmed Launch Day",
            "spacex_next_confirmed_launch_day",
            "mdi:calendar",
            "spacexlaunch"
        )
    )

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Next Confirmed Launch Time",
            "spacex_next_confirmed_launch_time",
            "mdi:clock-outline",
            "spacexlaunch"
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

    async_add_entities(sensors)


class SpaceXSensor(CoordinatorEntity):
    """Defines a SpaceX Binary sensor."""

    def __init__(
        self, 
        coordinator: SpaceXUpdateCoordinator, 
        name: str, 
        entity_id: str, 
        icon:str, 
        device_identifier:str,
        ):
        """Initialize Entities."""

        super().__init__(coordinator=coordinator)

        self._name = name
        self._unique_id = f"spacex_{entity_id}"
        self._state = None
        self._icon = icon
        self._kind = entity_id
        self._device_identifier = device_identifier
        self._unit_of_measure = None
        self.attrs = {}

        if self._kind == "spacex_starman_speed":
            self._unit_of_measure = SPEED_KILOMETERS_PER_HOUR

        elif self._kind == "spacex_starman_distance":
            self._unit_of_measure = LENGTH_KILOMETERS


    @property
    def unique_id(self):
        """Return the unique Home Assistant friendly identifier for this entity."""
        return self._unique_id

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
    def extra_state_attributes(self):
        """Return the attributes."""
        coordinator_data = self.coordinator.data
        starman_data = coordinator_data["starman"]
        launch_data = coordinator_data["next_launch"]
        latest_launch_data = coordinator_data["latest_launch"]

        if self._kind == "spacex_next_launch_mission":
            self.attrs["mission_patch"] = launch_data["links"].get("patch",{}).get("large")
            if launch_data.get("details"):
                self.attrs["details"] = launch_data["details"][0:255]
                if len(launch_data["details"]) > 255:
                    self.attrs["details2"] = launch_data["details"][255:510]
                else:
                    self.attrs["details2"] = ""
                if len(launch_data["details"]) > 510:
                    self.attrs["details3"] = launch_data["details"][510:765]
                else:
                    self.attrs["details3"] = ""
            self.attrs["video_link"] = launch_data["links"].get("webcast")

        elif self._kind == "spacex_next_launch_day":
            self.attrs["launch_date_unix"] = launch_data["date_unix"]
            self.attrs["launch_date_utc"] = launch_data["date_utc"]

        elif self._kind == "spacex_next_launch_time":
            self.attrs["launch_time_24h"] = self._state = as_local(utc_from_timestamp(
                launch_data["date_unix"]
            )).strftime("%H:%M")

        elif self._kind == "spacex_next_launch_countdown":
            if launch_data["tbd"]:
                self.attrs["t0_countdown"] = "NA"
            else:
                t0_countdown = int(launch_data["date_unix"]) - int(time.time())
                day = t0_countdown // (24 * 3600)
                t0_countdown = t0_countdown % (24 * 3600)
                hour = t0_countdown // 3600
                t0_countdown %= 3600
                minutes = t0_countdown // 60
                t0_countdown %= 60
                seconds = t0_countdown

                countdown_string = ""
                if day > 0:
                    countdown_string = f"{day} days, "

                if hour > 0:
                    countdown_string = f"{countdown_string}{hour} hours, "

                if minutes > 0:
                    countdown_string = f"{countdown_string}{minutes} minutes, "

                countdown_string = f"{countdown_string}{seconds} seconds until the launch of {launch_data['name']}."
                
                self.attrs["t0_countdown"] = countdown_string

        elif self._kind == "spacex_next_confirmed_launch_day":
            if launch_data["tbd"]:
                self.attrs["launch_date_unix"] = "NA"
                self.attrs["launch_date_utc"] = "NA"
            else:
                self.attrs["launch_date_unix"] = launch_data["date_unix"]
                self.attrs["launch_date_utc"] = launch_data["date_utc"]

        elif self._kind == "spacex_next_confirmed_launch_time":
            self.attrs["launch_time_24h"] = self._state = as_local(utc_from_timestamp(
                launch_data["date_unix"]
            )).strftime("%H:%M")

        elif self._kind == "spacex_next_launch_site":
            self.attrs["short_name"] = launch_data["launch_site"]["name"]

        elif self._kind == "spacex_next_launch_rocket":
            core_counter = 1
            for this_core in launch_data["cores_detail"]:
                if this_core.get("details"):
                    self.attrs["core_" + str(core_counter) + "_serial"] = this_core["details"].get("serial")
                    self.attrs["core_" + str(core_counter) + "_block"] = this_core["details"].get("block")

                self.attrs["core_" + str(core_counter) + "_flight"] = this_core.get(
                    "flight"
                )
                
                self.attrs[
                    "core_" + str(core_counter) + "_landing_intent"
                ] = this_core.get("landing_attempt")
                
                if this_core.get("landpad"):
                    self.attrs["core_" + str(core_counter) + "_lz"] = this_core["landpad"][
                        "name"
                    ]
                    self.attrs["core_" + str(core_counter) + "_lz_long"] = this_core["landpad"][
                        "full_name"
                    ]
                else:
                    self.attrs["core_" + str(core_counter) + "_lz"] = "NA"
                    self.attrs["core_" + str(core_counter) + "_lz_long"] = "NA"
                
                core_counter = core_counter + 1

            if launch_data.get("fairings"):
                self.attrs["fairings_reused"] = launch_data.get("fairings",{}).get(
                    "reused"
                )
            else:
                self.attrs["fairings_reused"] = "NA"
        
        elif self._kind == "spacex_next_launch_payload":
            if len(launch_data["payloads_detail"]):
                if len(launch_data["payloads_detail"][0]["nationalities"]):
                    self.attrs["nationality"] = launch_data["payloads_detail"][0]["nationalities"][0]
                else:
                    self.attrs["nationality"] = "NA"
                if len(launch_data["payloads_detail"][0]["manufacturers"]):
                    self.attrs["manufacturer"] = launch_data["payloads_detail"][0]["manufacturers"][0]
                else:
                    self.attrs["manufacturer"] = "NA"

            if launch_data["payloads_detail"]:
                self.attrs["payload_type"] = launch_data["payloads_detail"][0]["type"]
                self.attrs["payload_mass"] = (
                    str(
                        launch_data["payloads_detail"][0]["mass_kg"]
                    )
                    + " kg"
                )
                self.attrs["payload_mass_us"] = (
                    str(
                        launch_data["payloads_detail"][0]["mass_lbs"]
                    )
                    + " lbs"
                )
                self.attrs["orbit"] = launch_data["payloads_detail"][0]["orbit"]
            else:
                self.attrs["payload_type"] = ""
                self.attrs["payload_mass"] = ""
                self.attrs["payload_mass_us"] = ""
           

        elif self._kind == "spacex_latest_launch_mission":
            self.attrs["mission_patch"] = latest_launch_data["links"].get("patch",{}).get("large")
            if latest_launch_data.get("details"):
                self.attrs["details"] = latest_launch_data["details"][0:255]
                if len(latest_launch_data["details"]) > 255:
                    self.attrs["details2"] = latest_launch_data["details"][255:510]
                else:
                    self.attrs["details2"] = ""
                if len(latest_launch_data["details"]) > 510:
                    self.attrs["details3"] = latest_launch_data["details"][510:765]
                else:
                    self.attrs["details3"] = ""
            self.attrs["video_link"] = latest_launch_data["links"].get("webcast")

        elif self._kind == "spacex_latest_launch_day":
            self.attrs["launch_date_unix"] = latest_launch_data["date_unix"]
            self.attrs["launch_date_utc"] = latest_launch_data["date_utc"]

        elif self._kind == "spacex_latest_launch_time":
            self.attrs["launch_time_24h"] = self._state = as_local(utc_from_timestamp(
                latest_launch_data["date_unix"]
            )).strftime("%H:%M")

        elif self._kind == "spacex_latest_launch_site":
            self.attrs["short_name"] = latest_launch_data["launch_site"]["name"]

        elif self._kind == "spacex_latest_launch_rocket":
            core_counter = 1
            for this_core in latest_launch_data["cores_detail"]:
                if this_core.get("details"):
                    self.attrs["core_" + str(core_counter) + "_serial"] = this_core.get("details",{}).get(
                        "serial"
                    )
                    self.attrs["core_" + str(core_counter) + "_block"] = this_core.get("details",{}).get(
                        "block"
                    )
                else:
                    self.attrs["core_" + str(core_counter) + "_serial"] = None
                    self.attrs["core_" + str(core_counter) + "_block"] = None

                self.attrs["core_" + str(core_counter) + "_flight"] = this_core.get(
                    "flight"
                )
                
                self.attrs[
                    "core_" + str(core_counter) + "_landing_intent"
                ] = this_core.get("landing_attempt")

                if this_core.get("landpad"):
                    self.attrs["core_" + str(core_counter) + "_lz"] = this_core.get("landpad",{}).get(
                        "name"
                    )

                    self.attrs["core_" + str(core_counter) + "_lz_long"] = this_core.get("landpad",{}).get(
                        "full_name"
                    )
                else:
                    self.attrs["core_" + str(core_counter) + "_lz"] = None
                    self.attrs["core_" + str(core_counter) + "_lz_long"] = None

                core_counter = core_counter + 1
            
            if latest_launch_data.get("fairings"):
                self.attrs["fairings_reused"] = latest_launch_data["fairings"].get(
                        "reused"
                    )

        elif self._kind == "spacex_latest_launch_payload":
            if len(latest_launch_data["payloads_detail"]):
                if len(latest_launch_data["payloads_detail"][0]["nationalities"]):
                    self.attrs["nationality"] = latest_launch_data["payloads_detail"][0]["nationalities"][0]
                else:
                    self.attrs["nationality"] = "NA"
                if len(latest_launch_data["payloads_detail"][0]["manufacturers"]):
                    self.attrs["manufacturer"] = latest_launch_data["payloads_detail"][0]["manufacturers"][0]
                else:
                    self.attrs["manufacturer"] = "NA"
                
                self.attrs["payload_type"] = latest_launch_data["payloads_detail"][0]["type"]
                self.attrs["payload_mass"] = (
                    str(
                        latest_launch_data["payloads_detail"][0]["mass_kg"]
                    )
                    + " kg"
                )
                self.attrs["payload_mass_us"] = (
                    str(
                        latest_launch_data["payloads_detail"][0]["mass_lbs"]
                    )
                    + " lbs"
                )
                self.attrs["orbit"] = latest_launch_data["payloads_detail"][0]["orbit"]


        elif self._kind == "spacex_starman_speed":
            self.attrs["machspeed"] = float(starman_data["speed_kph"]) / 1235

        elif self._kind == "spacex_starman_distance":
            self.attrs["au_distance"] = float(starman_data["earth_distance_km"]) / (1.496 * (10**8))

        return self.attrs

    @property
    def device_info(self):
        """Define the device based on device_identifier."""

        device_name = "SpaceX Launches"
        device_model = "Launch"

        if self._device_identifier != "spacexlaunch":
            device_name = "SpaceX Starman"
            device_model = "Starman"

        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._device_identifier)},
            ATTR_NAME: device_name,
            ATTR_MANUFACTURER: "SpaceX",
            ATTR_MODEL: device_model,
        }

    @property
    def state(self):
        """Return the state."""
        coordinator_data = self.coordinator.data
        starman_data = coordinator_data["starman"]
        launch_data = coordinator_data["next_launch"]
        latest_launch_data = coordinator_data["latest_launch"]

        if self._kind == "spacex_next_launch_mission":
            self._state = launch_data["name"]

        elif self._kind == "spacex_next_launch_day":
            self._state = as_local(utc_from_timestamp(
                launch_data["date_unix"]
            )).strftime("%d-%b-%Y")
            
        elif self._kind == "spacex_next_launch_time":
            self._state = as_local(utc_from_timestamp(
                launch_data["date_unix"]
            )).strftime("%I:%M %p")

        elif self._kind == "spacex_next_launch_countdown":
            if launch_data["tbd"]:
                self._state = None
            else:
                t0_countdown = int(launch_data["date_unix"]) - int(time.time())
                self._state = str(datetime.timedelta(seconds=t0_countdown))

        elif self._kind == "spacex_next_confirmed_launch_day":
            if launch_data["tbd"]:
                self._state = None
            else:
                self._state = as_local(utc_from_timestamp(
                    launch_data["date_unix"]
                )).strftime("%d-%b-%Y")

        elif self._kind == "spacex_next_confirmed_launch_time":
            if launch_data["tbd"]:
                self._state = None
            else:
                self._state = as_local(utc_from_timestamp(
                    launch_data["date_unix"]
                )).strftime("%I:%M %p")

        elif self._kind == "spacex_next_launch_site":
            self._state = launch_data["launch_site"]["full_name"]

        elif self._kind == "spacex_next_launch_rocket":
            self._state = launch_data["rocket"]["name"]

        elif self._kind == "spacex_next_launch_payload":
            if launch_data["payloads_detail"]:
                self._state = launch_data["payloads_detail"][0]["name"]
            else:
                self._state = ""

        elif self._kind == "spacex_latest_launch_mission":
            self._state = latest_launch_data["name"]
            
        elif self._kind == "spacex_latest_launch_day":
            self._state = as_local(utc_from_timestamp(
                latest_launch_data["date_unix"]
            )).strftime("%d-%b-%Y")
            
        elif self._kind == "spacex_latest_launch_time":
            self._state = as_local(utc_from_timestamp(
                latest_launch_data["date_unix"]
            )).strftime("%I:%M %p")

        elif self._kind == "spacex_latest_launch_site":
            self._state = latest_launch_data["launch_site"]["full_name"]

        elif self._kind == "spacex_latest_launch_rocket":
            self._state = latest_launch_data["rocket"]["name"]
            
        elif self._kind == "spacex_latest_launch_payload":
            self._state = latest_launch_data["payloads_detail"][0]["name"]
            
        elif self._kind == "spacex_starman_speed":
            self._state = int(starman_data["speed_kph"])
            self._unit_of_measure = SPEED_KILOMETERS_PER_HOUR

        elif self._kind == "spacex_starman_distance":
            self._state = int(starman_data["earth_distance_km"])
            self._unit_of_measure = LENGTH_KILOMETERS
            
        return self._state

    async def async_update(self):
        """Update SpaceX Binary Sensor Entity."""
        await self.coordinator.async_request_refresh()
        _LOGGER.debug("Updating state of the sensors.")
        
    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
