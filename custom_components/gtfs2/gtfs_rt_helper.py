import logging
from datetime import datetime, timedelta
import json
import os

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import requests
import voluptuous as vol
from google.transit import gtfs_realtime_pb2
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, CONF_NAME
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

from .const import (

    ATTR_STOP_ID,
    ATTR_ROUTE,
    ATTR_TRIP,
    ATTR_DIRECTION_ID,
    ATTR_DUE_IN,
    ATTR_DUE_AT,
    ATTR_DELAY,
    ATTR_NEXT_UP,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    ATTR_DEVICE_CLASS,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,

    CONF_API_KEY,
    CONF_X_API_KEY,
    CONF_API_KEY_LOCATION,
    CONF_STOP_ID,
    CONF_ROUTE,
    CONF_TRIP_UPDATE_URL,
    CONF_VEHICLE_POSITION_URL,
    CONF_ROUTE_DELIMITER,
    CONF_ICON,
    CONF_SERVICE_TYPE,

    DEFAULT_SERVICE,
    DEFAULT_ICON,
    DEFAULT_DIRECTION,
    DEFAULT_PATH,
    DEFAULT_PATH_GEOJSON,

    TIME_STR_FORMAT
)

def due_in_minutes(timestamp):
    """Get the remaining minutes from now until a given datetime object."""
    diff = timestamp - dt_util.now().replace(tzinfo=None)
    return int(diff.total_seconds() / 60)

def get_gtfs_feed_entities(url: str, headers, label: str):
    _LOGGER.debug(f"GTFS RT get_feed_entities for url: {url} , headers: {headers}, label: {label}")
    feed = gtfs_realtime_pb2.FeedMessage()  # type: ignore

    # TODO add timeout to requests call
    response = requests.get(url, headers=headers, timeout=20)
    if response.status_code == 200:
        _LOGGER.debug("Successfully updated %s", label)
    else:
        _LOGGER.debug("Updating %s, and got: %s for: %s", label, response.status_code, response.content)

    if label == "alerts":
        _LOGGER.debug("Feed : %s", feed)
    feed.ParseFromString(response.content) 
    return feed.entity

def get_next_services(self):
    self.data = self._get_rt_trip_statuses
    self._stop = self._stop_id
    self._destination = self._destination_id
    self._route = self._route_id
    self._trip = self._trip_id
    self._direction = self._direction
    self.delay = "unknown"
    _LOGGER.debug("Configuration for RT route: %s, RT trip: %s, RT stop: %s, RT direction: %s", self._route, self._trip, self._stop, self._direction)
    next_services = self.data.get(self._trip, {}).get(self._direction, {}).get(self._stop, [])
    if not next_services:
        # GTFS RT feed may differ, try via route
        self._direction = '0'
        self.data2 = get_rt_route_statuses(self)
        next_services = self.data2.get(self._route, {}).get(self._direction, {}).get(self._stop, [])  
        _LOGGER.debug("Next Services, using route_id instead of trip_id: %s", next_services)
    if next_services:
        _LOGGER.debug("Next services: %s", next_services[0])
        delay = next_services[0].delay

    if self.hass.config.time_zone is None:
        _LOGGER.error("Timezone is not set in Home Assistant configuration, using UTC instead")
        timezone = "UTC"
    else:
        timezone=dt_util.get_time_zone(self.hass.config.time_zone)
    
    if self._relative :
        due_in = (
            due_in_minutes(next_services[0].arrival_time)
            if len(next_services) > 0
            else "-"
        )
    else:
        due_in = (
            dt_util.as_utc(next_services[0].arrival_time)
            if len(next_services) > 0
            else "-"
        )
    
    attrs = {
        ATTR_DUE_IN: due_in,
        ATTR_DELAY: self.delay,
        ATTR_STOP_ID: self._stop,
        ATTR_ROUTE: self._route,
        ATTR_TRIP: self._trip,
        ATTR_DIRECTION_ID: self._direction,
        ATTR_LATITUDE: "",
        ATTR_LONGITUDE: ""
    }
    if len(next_services) > 0:
        attrs[ATTR_DUE_AT] = (
            next_services[0].arrival_time.strftime(TIME_STR_FORMAT)
            if len(next_services) > 0
            else "-"
        )
        if next_services[0].position:
            if next_services[0].position[0]:
                attrs[ATTR_LATITUDE] = next_services[0].position[0][1]
                attrs[ATTR_LONGITUDE] = next_services[0].position[0][0]
    if len(next_services) > 1:
        attrs[ATTR_NEXT_UP] = (
            next_services[1].arrival_time.strftime(TIME_STR_FORMAT)
            if len(next_services) > 1
            else "-"
        )
    if self._relative :
        attrs[ATTR_UNIT_OF_MEASUREMENT] = "min"
    else :
        attrs[ATTR_DEVICE_CLASS] = (
            "timestamp" 
            if len(next_services) > 0
            else ""
        )

    _LOGGER.debug("Next services attributes: %s", attrs)
    return attrs
    
def get_rt_route_statuses(self):
    vehicle_positions = {}
    
    if (self._vehicle_position_url)[:4] == "http" :   
        vehicle_positions = get_rt_vehicle_positions(self)
              
    class StopDetails:
        def __init__(self, arrival_time, delay, position):
            self.arrival_time = arrival_time
            self.delay = delay
            self.position = position

    departure_times = {}

    feed_entities = get_gtfs_feed_entities(
        url=self._trip_update_url, headers=self._headers, label="trip data"
    )
    self._feed_entities = feed_entities
    _LOGGER.debug("Departure times searching for route: %s", self._route_id)
    for entity in feed_entities:
        if entity.HasField("trip_update"):
            
            # If delimiter specified split the route ID in the gtfs rt feed
            if self._route_delimiter is not None:
                route_id_split = entity.trip_update.trip.route_id.split(
                    self._route_delimiter
                )
                if route_id_split[0] == self._route_delimiter:
                    route_id = entity.trip_update.trip.route_id
                else:
                    route_id = route_id_split[0]
                _LOGGER.debug("Feed route_id: %s, changed to: %s", entity.trip_update.trip.route_id, route_id)
            else:
                route_id = entity.trip_update.trip.route_id
            if route_id == self._route_id:
                _LOGGER.debug("Route Statuses Entity: %s", entity)
                
                if route_id not in departure_times:
                    departure_times[route_id] = {}
                
                if entity.trip_update.trip.direction_id is not None:
                    direction_id = str(entity.trip_update.trip.direction_id)
                else:
                    direction_id = DEFAULT_DIRECTION
                if direction_id not in departure_times[route_id]:
                    departure_times[route_id][direction_id] = {}

                for stop in entity.trip_update.stop_time_update:
                    stop_id = stop.stop_id
                    if not departure_times[route_id][direction_id].get(
                        stop_id
                    ):
                        departure_times[route_id][direction_id][stop_id] = []
                    # Use stop arrival time;
                    # fall back on departure time if not available
                    if stop.arrival.time == 0:
                        stop_time = stop.departure.time
                    else:
                        stop_time = stop.arrival.time
                        
                    delay = 'unknown'
                    try:
                        delay = stop.arrival.delay
                    except:
                        delay = 'unknown'
                    # Ignore arrival times in the past
                    if due_in_minutes(datetime.fromtimestamp(stop_time)) >= 0:
                        details = StopDetails(
                            datetime.fromtimestamp(stop_time),delay,
                            [d["properties"].get(entity.trip_update.trip.trip_id) for d in vehicle_positions],
                        )
                        departure_times[route_id][direction_id][
                            stop_id
                        ].append(details)

    # Sort by arrival time
    for route in departure_times:
        for direction in departure_times[route]:
            for stop in departure_times[route][direction]:
                departure_times[route][direction][stop].sort(
                    key=lambda t: t.arrival_time
                )

    self.info = departure_times
    _LOGGER.debug("Departure times Route: %s", departure_times)
    return departure_times
    
def get_rt_trip_statuses(self):

    vehicle_positions = {}
    
    if (self._vehicle_position_url)[:4] == "http" :   
        vehicle_positions = get_rt_vehicle_positions(self)
              
    class StopDetails:
        def __init__(self, arrival_time, delay, position):
            self.arrival_time = arrival_time
            self.delay = delay
            self.position = position

    departure_times = {}
    
    feed_entities = get_gtfs_feed_entities(
        url=self._trip_update_url, headers=self._headers, label="trip data"
    )
    self._feed_entities = feed_entities
    _LOGGER.debug("Departure times searching for trip: %s", self._trip_id)
    for entity in feed_entities:

        if entity.HasField("trip_update"):
            
            trip_id = entity.trip_update.trip.trip_id   
            
            if trip_id == self._trip_id:
                _LOGGER.debug("Trip Statuses Entity: %s", entity)

                if trip_id not in departure_times:
                    departure_times[trip_id] = {}
                
                if entity.trip_update.trip.direction_id is not None:
                    direction_id = str(entity.trip_update.trip.direction_id)
                else:
                    direction_id = DEFAULT_DIRECTION
                if direction_id not in departure_times[trip_id]:
                    departure_times[trip_id][direction_id] = {}

                for stop in entity.trip_update.stop_time_update:
                    stop_id = stop.stop_id
                    if not departure_times[trip_id][direction_id].get(
                        stop_id
                    ):
                        departure_times[trip_id][direction_id][stop_id] = []
                    # Use stop arrival time;
                    # fall back on departure time if not available
                    if stop.arrival.time == 0:
                        stop_time = stop.departure.time
                    else:
                        stop_time = stop.arrival.time
                    try:
                        delay = stop.arrival.delay
                    except:
                        delay = 'unknown'
                    # Ignore arrival times in the past
                    if due_in_minutes(datetime.fromtimestamp(stop_time)) >= 0:
                        details = StopDetails(
                            datetime.fromtimestamp(stop_time),delay,
                            [d["properties"].get(entity.trip_update.trip.trip_id) for d in vehicle_positions],
                        )
                        departure_times[trip_id][direction_id][
                            stop_id
                        ].append(details)

    # Sort by arrival time
    for trip in departure_times:
        for direction in departure_times[trip]:
            for stop in departure_times[trip][direction]:
                departure_times[trip][direction][stop].sort(
                    key=lambda t: t.arrival_time
                )

    self.info = departure_times
    _LOGGER.debug("Departure times Trip: %s", departure_times)
    return departure_times    

def get_rt_vehicle_positions(self):
    feed_entities = get_gtfs_feed_entities(
        url=self._vehicle_position_url,
        headers=self._headers,
        label="vehicle positions",
    )
    geojson_body = []
    geojson_element = {"geometry": {"coordinates":[],"type": "Point"}, "properties": {"id": "", "title": "", "trip_id": "", "route_id": "", "direction_id": "", "vehicle_id": "", "vehicle_label": ""}, "type": "Feature"}
    for entity in feed_entities:
        vehicle = entity.vehicle
        
        if not vehicle.trip.trip_id:
            # Vehicle is not in service
            continue
        if vehicle.trip.trip_id == self._trip_id:  
            _LOGGER.debug("Adding position for TripId: %s, RouteId: %s, DirectionId: %s, Lat: %s, Lon: %s", vehicle.trip.trip_id, vehicle.trip.route_id, vehicle.trip.direction_id, vehicle.position.latitude, vehicle.position.longitude)  
            
        # add data if in the selected direction
        if (str(self._route_id) == str(vehicle.trip.route_id) or str(vehicle.trip.trip_id) == str(self._trip_id)) and str(self._direction) == str(vehicle.trip.direction_id):
            _LOGGER.debug("Found vehicle on route with attributes: %s", vehicle)
            geojson_element = {"geometry": {"coordinates":[],"type": "Point"}, "properties": {"id": "", "title": "", "trip_id": "", "route_id": "", "direction_id": "", "vehicle_id": "", "vehicle_label": ""}, "type": "Feature"}
            geojson_element["geometry"]["coordinates"] = []
            geojson_element["geometry"]["coordinates"].append(vehicle.position.longitude)
            geojson_element["geometry"]["coordinates"].append(vehicle.position.latitude)
            geojson_element["properties"]["id"] = str(self._route_id) + "(" + str(vehicle.trip.direction_id) + ")" + str(vehicle.trip.trip_id)[-3:]
            geojson_element["properties"]["title"] = str(self._route_id) + "(" + str(vehicle.trip.direction_id) + ")" + str(vehicle.trip.trip_id)[-3:]
            geojson_element["properties"]["trip_id"] = vehicle.trip.trip_id
            geojson_element["properties"]["route_id"] = str(self._route_id)
            geojson_element["properties"]["direction_id"] = vehicle.trip.direction_id
            geojson_element["properties"]["vehicle_id"] = vehicle.vehicle.id
            geojson_element["properties"]["vehicle_label"] = vehicle.vehicle.label
            geojson_element["properties"][vehicle.trip.trip_id] = geojson_element["geometry"]["coordinates"]
            geojson_body.append(geojson_element)
    
    self.geojson = {"features": geojson_body, "type": "FeatureCollection"}
        
    _LOGGER.debug("Vehicle geojson: %s", json.dumps(self.geojson))
    self._route_dir = str(self._route_id) + "_" + str(self._direction)
    update_geojson(self)
    return geojson_body
    
def get_rt_alerts(self):
    rt_alerts = {}
    if (self._alerts_url)[:4] == "http":
        feed_entities = get_gtfs_feed_entities(
            url=self._alerts_url,
            headers=self._headers,
            label="alerts",
        )
        for entity in feed_entities:
            if entity.HasField("alert"):
                for x in entity.alert.informed_entity:
                    if x.HasField("stop_id"):
                        stop_id = x.stop_id 
                    else:
                        stop_id = "unknown"
                    if x.HasField("stop_id"):
                        route_id = x.route_id  
                    else:
                        route_id = "unknown"
                if stop_id == self._stop_id and (route_id == "unknown" or route_id == self._route_id): 
                    _LOGGER.debug("RT Alert for route: %s, stop: %s, alert: %s", route_id, stop_id, entity.alert.header_text)
                    rt_alerts["origin_stop_alert"] = (str(entity.alert.header_text).split('text: "')[1]).split('"',1)[0].replace(':','').replace('\n','')
                if stop_id == self._destination_id and (route_id == "unknown" or route_id == self._route_id): 
                    _LOGGER.debug("RT Alert for route: %s, stop: %s, alert: %s", route_id, stop_id, entity.alert.header_text)
                    rt_alerts["destination_stop_alert"] = (str(entity.alert.header_text).split('text: "')[1]).split('"',1)[0].replace(':','').replace('\n','')
                if stop_id == "unknown" and route_id == self._route_id: 
                    _LOGGER.debug("RT Alert for route: %s, stop: %s, alert: %s", route_id, stop_id, entity.alert.header_text)
                    rt_alerts["origin_stop_alert"] = (str(entity.alert.header_text).split('text: "')[1]).split('"',1)[0].replace(':','').replace('\n','')
                    rt_alerts["destination_stop_alert"] = (str(entity.alert.header_text).split('text: "')[1]).split('"',1)[0].replace(':','').replace('\n','')    
                        
    return rt_alerts
    
    
def update_geojson(self):    
    geojson_dir = self.hass.config.path(DEFAULT_PATH_GEOJSON)
    os.makedirs(geojson_dir, exist_ok=True)
    file = os.path.join(geojson_dir, self._route_dir + ".json")
    _LOGGER.debug("Creating geojson file: %s", file)
    with open(file, "w") as outfile:
        json.dump(self.geojson, outfile)
    
def get_gtfs_rt(hass, path, data):
    """Get gtfs rt data."""
    _LOGGER.debug("Getting gtfs rt locally with data: %s", data)
    gtfs_dir = hass.config.path(path)
    os.makedirs(gtfs_dir, exist_ok=True)
    url = data["url"]
    file = data["file"] + ".rt"
    try:
        r = requests.get(url, allow_redirects=True)
        open(os.path.join(gtfs_dir, file), "wb").write(r.content)
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.error("Ìssues with downloading GTFS RT data to: %s", os.path.join(gtfs_dir, file))
        return "no_rt_data_file"
    return "ok"       
        
