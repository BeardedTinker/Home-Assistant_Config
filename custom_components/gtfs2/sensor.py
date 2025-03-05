"""Support for GTFS."""
from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_ARRIVAL,
    ATTR_BICYCLE,
    ATTR_DAY,
    ATTR_DUE_IN,
    ATTR_NEXT_RT,
    ATTR_NEXT_RT_DELAYS,
    ATTR_DROP_OFF_DESTINATION,
    ATTR_DROP_OFF_ORIGIN,
    ATTR_FIRST,
    ATTR_RT_UPDATED_AT,
    ATTR_INFO,
    ATTR_INFO_RT,
    ATTR_LAST,
    ATTR_LOCATION_DESTINATION,
    ATTR_LOCATION_ORIGIN,
    ATTR_OFFSET,
    ATTR_PICKUP_DESTINATION,
    ATTR_PICKUP_ORIGIN,
    ATTR_ROUTE_TYPE,
    ATTR_TIMEPOINT_DESTINATION,
    ATTR_TIMEPOINT_ORIGIN,
    ATTR_WHEELCHAIR,
    ATTR_WHEELCHAIR_DESTINATION,
    ATTR_WHEELCHAIR_ORIGIN,
    ATTR_TIMEZONE_ORIGIN,
    ATTR_TIMEZONE_DESTINATION,
    BICYCLE_ALLOWED_DEFAULT,
    BICYCLE_ALLOWED_OPTIONS,
    DEFAULT_NAME,
    DOMAIN,
    DROP_OFF_TYPE_DEFAULT,
    DROP_OFF_TYPE_OPTIONS,
    ICON,
    ICONS,
    LOCATION_TYPE_DEFAULT,
    LOCATION_TYPE_OPTIONS,
    PICKUP_TYPE_DEFAULT,
    PICKUP_TYPE_OPTIONS,
    ROUTE_TYPE_OPTIONS,
    TIMEPOINT_DEFAULT,
    TIMEPOINT_OPTIONS,
    TIME_STR_FORMAT,                    
    WHEELCHAIR_ACCESS_DEFAULT,
    WHEELCHAIR_ACCESS_OPTIONS,
    WHEELCHAIR_BOARDING_DEFAULT,
    WHEELCHAIR_BOARDING_OPTIONS,
)
from .coordinator import GTFSUpdateCoordinator, GTFSLocalStopUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    ) -> None:
    """Initialize the setup."""   
    if config_entry.data.get('device_tracker_id',None):
        sensors = []
        coordinator: GTFSLocalStopUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][
           "coordinator"
        ]
        await coordinator.async_config_entry_first_refresh()
        if not coordinator.data["extracting"]:
            for stop in coordinator.data["local_stops_next_departures"]:
                sensors.append(
                        GTFSLocalStopSensor(stop, coordinator, coordinator.data.get("name", "No Name"))
                    )
        
    else:
        coordinator: GTFSUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][
           "coordinator"
        ]
        await coordinator.async_config_entry_first_refresh()
        
        sensors = [
            GTFSDepartureSensor(coordinator),
        ]

    async_add_entities(sensors, False)
    
class GTFSDepartureSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a GTFS departure sensor."""

    def __init__(self, coordinator) -> None:
        """Initialize the GTFSsensor."""
        super().__init__(coordinator)
        self._name = coordinator.data["name"]
        self._attributes: dict[str, Any] = {}

        self._attr_unique_id = f"gtfs-{self._name}"
        self._attr_device_info = DeviceInfo(
            name=f"GTFS - {self._name}",
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"GTFS - {self._name}")},
            manufacturer="GTFS",
            model=self._name,
        )
        self._attributes = self._update_attrs()
        self._attr_extra_state_attributes = self._attributes

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_attrs()
        super()._handle_coordinator_update()

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return self._icon

    def _update_attrs(self):  # noqa: C901 PLR0911
        _LOGGER.debug("SENSOR update attr data: %s", self.coordinator.data)
        if self.coordinator.data["extracting"]:  
            _LOGGER.warning("Extracting datasource: %s ,for sensor: %s", self.coordinator.data["file"], self._name)
            self._attr_native_value = None
            return
        self._pygtfs = self.coordinator.data["schedule"]
        self.extracting = self.coordinator.data["extracting"]
        self.origin = self.coordinator.data["origin"].split(": ")[0]
        self.destination = self.coordinator.data["destination"].split(": ")[0]
        self._include_tomorrow = self.coordinator.data["include_tomorrow"]
        self._offset = self.coordinator.data["offset"]
        self._departure = self.coordinator.data.get("next_departure",None)
        self._departure_rt = self.coordinator.data.get("next_departure_realtime_attr",None)
        self._route_type = self.coordinator.data["route_type"]
        self._available = False
        self._icon = ICON
        self._state: datetime.datetime | None = None
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._trip = None
        self._route = None
        self._agency = None
        self._origin = None
        self._destination = None        
        # Fetch valid stop information once
        # exclude check if route_type =2 (trains) as no ID is used
        if not self._origin and not self.extracting and self._route_type != "2":
            stops = self._pygtfs.stops_by_id(self.origin)
            if not stops:
                self._available = False
                _LOGGER.warning("Origin stop ID %s not found", self.origin)
                return
            self._origin = stops[0]
        else: 
            self._origin = self.origin
        # exclude check if route_type =2 (trains) as no ID is used
        if not self._destination and not self.extracting and self._route_type != "2":
            stops = self._pygtfs.stops_by_id(self.destination)
            if not stops:
                self._available = False
                _LOGGER.warning(
                    "Destination stop ID %s not found", self.destination
                )
                return
            self._destination = stops[0]
        else:
            self._destination = self.destination

        # Fetch trip and route details once, unless updated
        if not self._departure:
            self._trip = None
        else:
            trip_id = self._departure.get("trip_id")
            if not self.extracting and (not self._trip or self._trip.trip_id != trip_id):
                _LOGGER.debug("Fetching trip details for %s", trip_id)
                self._trip = self._pygtfs.trips_by_id(trip_id)[0]

            route_id = self._departure.get("route_id")
            if not self.extracting and (not self._route or self._route.route_id != route_id):
                _LOGGER.debug("Fetching route details for %s", route_id)
                self._route = self._pygtfs.routes_by_id(route_id)[0]

        # fetch next departures
        self._departure = self.coordinator.data["next_departure"]
        if not self._departure:
            self._next_departures = None
        else:
            self._next_departures = self._departure.get("next_departures",None)

        # Fetch agency details exactly once
        if self._agency is None and self._route:
            _LOGGER.debug("Fetching agency details for %s", self._route.agency_id)
            try:
                self._agency = self._pygtfs.agencies_by_id(self._route.agency_id)[0]
            except IndexError:
                _LOGGER.debug(
                    (
                        "Agency ID '%s' was not found in agency table, "
                        "you may want to update the routes database table "
                        "to fix this missing reference"
                    ),
                    self._route.agency_id,
                )
                self._agency = False

        # Define the state as a Agency TZ, then help TZ (which is UTC if no HA TZ set)
        if not self._departure:
            self._state = None
        #elif self._agency:
        #    _LOGGER.debug(
        #        "Self._departure time for state value TZ: %s ",
        #        {self._departure.get("departure_time")},
        #    )
        #    self._state = self._departure["departure_time"].replace(
        #        tzinfo=dt_util.get_time_zone(self._agency.agency_timezone)
        #    )
        else:
            _LOGGER.debug(
                "Self._departure time from helper: %s",
                {self._departure.get("departure_time")},
            )
            self._state = self._departure.get("departure_time")
            
        # settin state value
        self._attr_native_value = self._state

        if self._agency:
            self._attr_attribution = self._agency.agency_name
        else:
            self._attr_attribution = None

        if self._route:
            self._icon = ICONS.get(self._route.route_type, ICON)
        else:
            self._icon = ICON

        name = (
            f"{getattr(self._agency, 'agency_name', DEFAULT_NAME)} "
            f"{self._origin} to {self._destination} next departure"
        )
        if not self._departure:
            name = f"{DEFAULT_NAME}"
        self._name = self._name or name

        # Add departure information
        if self._departure:
            self._attributes[ATTR_ARRIVAL] = dt_util.as_utc(
                self._departure.get("arrival_time")
            ).isoformat()

            self._attributes[ATTR_DAY] = self._departure["day"]

            if self._departure[ATTR_FIRST] is not None:
                self._attributes[ATTR_FIRST] = self._departure["first"]
            elif ATTR_FIRST in self._attributes:
                del self._attributes[ATTR_FIRST]

            if self._departure[ATTR_LAST] is not None:
                self._attributes[ATTR_LAST] = self._departure["last"]
            elif ATTR_LAST in self._attributes:
                del self._attributes[ATTR_LAST]
        else:
            if ATTR_ARRIVAL in self._attributes:
                del self._attributes[ATTR_ARRIVAL]
            if ATTR_DAY in self._attributes:
                del self._attributes[ATTR_DAY]
            if ATTR_FIRST in self._attributes:
                del self._attributes[ATTR_FIRST]
            if ATTR_LAST in self._attributes:
                del self._attributes[ATTR_LAST]

        # Add contextual information
        self._attributes[ATTR_OFFSET] = self._offset

        if self._state is None:
            self._attributes[ATTR_INFO] = (
                "No more departures or extracting new data"
                if self._include_tomorrow
                else "No more departures today or extracting new data"
            )
        elif ATTR_INFO in self._attributes:
            del self._attributes[ATTR_INFO]

        # Add extra metadata
        key = "agency_id"
        if self._agency and key not in self._attributes:
            self.append_keys(self.dict_for_table(self._agency), "Agency")

        key = "origin_station_stop_id"
        # exclude check if route_type =2 (trains) as no ID is used
        if self._route_type != "2":
            if self._origin and key not in self._attributes:
                self.append_keys(self.dict_for_table(self._origin), "Origin Station")
                self._attributes[ATTR_LOCATION_ORIGIN] = LOCATION_TYPE_OPTIONS.get(
                    self._origin.location_type, LOCATION_TYPE_DEFAULT
                )
                self._attributes[ATTR_WHEELCHAIR_ORIGIN] = WHEELCHAIR_BOARDING_OPTIONS.get(
                    self._origin.wheelchair_boarding, WHEELCHAIR_BOARDING_DEFAULT
                )
        else:
            self._attributes["origin_station_stop_name"] = self._departure.get("origin_stop_name", None)
            self._attributes["origin_station_stop_id"] =  self._departure.get("origin_stop_id", None)
            self._attributes["origin_station_stop_sequence"] =  self._departure.get("origin_stop_sequence", None)

        key = "destination_station_stop_id"
        # exclude check if route_type =2 (trains) as no ID is used
        if self._route_type != "2":
            if self._destination and key not in self._attributes:
                self.append_keys(
                    self.dict_for_table(self._destination), "Destination Station"
                )
                self._attributes[ATTR_LOCATION_DESTINATION] = LOCATION_TYPE_OPTIONS.get(
                    self._destination.location_type, LOCATION_TYPE_DEFAULT
                )
                self._attributes[
                    ATTR_WHEELCHAIR_DESTINATION
                ] = WHEELCHAIR_BOARDING_OPTIONS.get(
                    self._destination.wheelchair_boarding, WHEELCHAIR_BOARDING_DEFAULT
                )
        else:
            self._attributes["destination_station_stop_name"] = self._departure.get("destination_stop_name", None)  
            self._attributes["destination_station_stop_id"] = self._departure.get("destination_stop_id", None)          

        # Manage Route metadata
        key = "route_id"
        if not self._route and key in self._attributes:
            self.remove_keys("Route")
        elif self._route and (
            key not in self._attributes or self._attributes[key] != self._route.route_id
        ):
            self.append_keys(self.dict_for_table(self._route), "Route")
            self._attributes[ATTR_ROUTE_TYPE] = ROUTE_TYPE_OPTIONS[
                self._route.route_type
            ]

        # Manage Trip metadata
        key = "trip_id"
        if not self._trip and key in self._attributes:
            self.remove_keys("Trip")
        elif self._trip and (
            key not in self._attributes or self._attributes[key] != self._trip.trip_id
        ):
            self.append_keys(self.dict_for_table(self._trip), "Trip")
            self._attributes[ATTR_BICYCLE] = BICYCLE_ALLOWED_OPTIONS.get(
                self._trip.bikes_allowed, BICYCLE_ALLOWED_DEFAULT
            )
            self._attributes[ATTR_WHEELCHAIR] = WHEELCHAIR_ACCESS_OPTIONS.get(
                self._trip.wheelchair_accessible, WHEELCHAIR_ACCESS_DEFAULT
            )

        # Manage Stop Times metadata
        prefix = "origin_stop"
        if self._departure:
            self.append_keys(self._departure["origin_stop_time"], prefix)
            self._attributes[ATTR_DROP_OFF_ORIGIN] = DROP_OFF_TYPE_OPTIONS.get(
                self._departure["origin_stop_time"]["Drop Off Type"],
                DROP_OFF_TYPE_DEFAULT,
            )
            self._attributes[ATTR_PICKUP_ORIGIN] = PICKUP_TYPE_OPTIONS.get(
                self._departure["origin_stop_time"]["Pickup Type"], PICKUP_TYPE_DEFAULT
            )
            self._attributes[ATTR_TIMEPOINT_ORIGIN] = TIMEPOINT_OPTIONS.get(
                self._departure["origin_stop_time"]["Timepoint"], TIMEPOINT_DEFAULT
            )
            self._attributes[ATTR_TIMEZONE_ORIGIN] = self._departure.get("origin_stop_timezone", None)
        else:
            self.remove_keys(prefix)
        
        if "destination_stop_time" in self._departure:
            _LOGGER.debug("Destination_stop_time %s", self._departure["destination_stop_time"])
        else:
            _LOGGER.debug("No destination_stop_time, possibly no service today")
        
        prefix = "destination_stop"
        if self._departure:
            self.append_keys(self._departure["destination_stop_time"], prefix)
            self._attributes[ATTR_DROP_OFF_DESTINATION] = DROP_OFF_TYPE_OPTIONS.get(
                self._departure["destination_stop_time"]["Drop Off Type"],
                DROP_OFF_TYPE_DEFAULT,
            )
            self._attributes[ATTR_PICKUP_DESTINATION] = PICKUP_TYPE_OPTIONS.get(
                self._departure["destination_stop_time"]["Pickup Type"],
                PICKUP_TYPE_DEFAULT,
            )
            self._attributes[ATTR_TIMEPOINT_DESTINATION] = TIMEPOINT_OPTIONS.get(
                self._departure["destination_stop_time"]["Timepoint"], TIMEPOINT_DEFAULT
            )
            self._attributes[ATTR_TIMEZONE_DESTINATION] = self._departure.get("destination_stop_timezone", None)
        else:
            self.remove_keys(prefix)

        # Add next departures
        prefix = "next_departures"
        self._attributes["next_departures"] = []
        if self._next_departures:
            self._attributes["next_departures"] = self._departure[
                "next_departures"][:10]
        # Add next departures with their lines
        prefix = "next_departures_lines"
        self._attributes["next_departures_lines"] = []
        if self._next_departures:
            self._attributes["next_departures_lines"] = self._departure[
                "next_departures_lines"][:10]                         
            
        # Add next departures with their headsign
        prefix = "next_departures_headsign"
        self._attributes["next_departures_headsign"] = []
        if self._next_departures:
            self._attributes["next_departures_headsign"] = self._departure[
                "next_departures_headsign"][:10] 

        self._attributes["gtfs_updated_at"] = self.coordinator.data[
            "gtfs_updated_at"]
        
        self._attributes["origin_stop_alert"] = self.coordinator.data[
            "alert"].get("origin_stop_alert", "no info")
        self._attributes["destination_stop_alert"] = self.coordinator.data[
            "alert"].get("destination_stop_alert", "no info")            
        
        if self._departure_rt:
            _LOGGER.debug("next dep realtime attr: %s", self._departure_rt)
            # Add next departure realtime to the right level, only if populated
            if "gtfs_rt_updated_at" in self._departure_rt:
                self._attributes["gtfs_rt_updated_at"] = self._departure_rt[ATTR_RT_UPDATED_AT]
                if self._departure_rt.get(ATTR_NEXT_RT, None):
                    self._attributes["next_departure_realtime"] = self._departure_rt[ATTR_NEXT_RT][0]
                    self._attributes["next_departures_realtime"] = self._departure_rt[ATTR_NEXT_RT]
                else:
                    self._attributes["next_departure_realtime"] = '-'
                    self._attributes["next_departures_realtime"] = '-'
                if self._departure_rt.get(ATTR_NEXT_RT_DELAYS, None):
                    self._attributes["next_delay_realtime"] = self._departure_rt[ATTR_NEXT_RT_DELAYS][0]
                    self._attributes["next_delays_realtime"] = self._departure_rt[ATTR_NEXT_RT_DELAYS]
                else:
                    self._attributes["next_delay_realtime"] = '-'
                    self._attributes["next_delays_realtime"] = '-'
            if ATTR_INFO_RT in self._attributes:
                del self._attributes[ATTR_INFO_RT]    
        else:
            _LOGGER.debug("No next departure realtime attributes")         
            self._attributes[ATTR_INFO_RT] = (
                "No realtime information"
            )
               
        self._attr_extra_state_attributes = self._attributes
        return self._attr_extra_state_attributes

    @staticmethod
    def dict_for_table(resource: Any) -> dict:
        """Return a dictionary for the SQLAlchemy resource given."""
        _dict = {}
        for column in resource.__table__.columns:
            _dict[column.name] = str(getattr(resource, column.name))
        return _dict

    def append_keys(self, resource: dict, prefix: str | None = None) -> None:
        """Properly format key val pairs to append to attributes."""
        for attr, val in resource.items():
            if val == "" or val is None or attr == "feed_id":
                continue
            key = attr
            if prefix and not key.startswith(prefix):
                key = f"{prefix} {key}"
            key = slugify(key)
            self._attributes[key] = val

    def remove_keys(self, prefix: str) -> None:
        """Remove attributes whose key starts with prefix."""
        self._attributes = {
            k: v for k, v in self._attributes.items() if not k.startswith(prefix)
        }


class GTFSLocalStopSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a GTFS local stops departures sensor."""

    def __init__(self, stop, coordinator, name) -> None:
        """Initialize the GTFSsensor."""
        super().__init__(coordinator)
        self._stop = stop
        self._name = self._stop["stop_id"] + "_local_stop_" + self.coordinator.data['device_tracker_id']
        self._attributes: dict[str, Any] = {}

        self._attr_unique_id = self._name
        self._attr_device_info = DeviceInfo(
            name=f"GTFS - {name}",
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"GTFS - {name}")},
            manufacturer="GTFS",
            model=name,
        )
        self._stop = stop
        self._attributes = self._update_attrs()
        self._attr_extra_state_attributes = self._attributes

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_attrs()
        super()._handle_coordinator_update()

    def _update_attrs(self):  # noqa: C901 PLR0911
        _LOGGER.debug("SENSOR: %s, update with attr data: %s", self._name, self.coordinator.data)
        self._departure = self.coordinator.data.get("local_stops_next_departures",None) 
        self._state: str | None = None
        # if no data or extracting, stop
        if self.coordinator.data["extracting"]:  
            _LOGGER.warning("Extracting datasource: %s ,for sensor: %s", self.coordinator.data["file"], self._name)
            self._attr_native_value = None
            return
        
        self._state = self._stop["stop_name"] + " (" +  str(dt_util.now().replace(tzinfo=None).strftime(TIME_STR_FORMAT)) + ")"

        self._attr_native_value = self._state        
        self._attributes["gtfs_updated_at"] = self.coordinator.data[
            "gtfs_updated_at"]  
        self._attributes["device_tracker_id"] = self.coordinator.data[
            "device_tracker_id"]
        self._attributes["offset"] = self.coordinator.data[
            "offset"]
        
        # Add next departures with their lines
        self._attributes["next_departures_lines"] = {}
        if self._departure:
            for stop in self._departure:
                if self._name.startswith(stop["stop_id"]):
                    self._attributes["next_departures_lines"] = stop["departure"]
                    self._attributes["latitude"] = stop["latitude"]  
                    self._attributes["longitude"] = stop["longitude"]  
                    
          
        self._attr_extra_state_attributes = self._attributes
        return self._attr_extra_state_attributes
