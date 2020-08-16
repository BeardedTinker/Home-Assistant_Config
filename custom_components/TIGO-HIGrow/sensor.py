"""Support for the LiLyGo TIGO HIgrow sensor."""
import logging
import json
import time
import paho.mqtt.client as mqtt
# from datetime import timedelta
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
   CONF_NAME, CONF_MONITORED_CONDITIONS
   )
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)
#MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=1000)

# Key: ['json_key', 'name', 'unit',  'icon']
SENSOR_TYPES = {
    'date': ['date','date', ' ',  'mdi:calendar'], 
    'time':['time', 'time', ' ',  'mdi:clock'],
    'sleep5Count':['sleep5Count','sleep5Count', ' ',  'mdi:counter'],
    'bootCount':['bootCount','bootCount', ' ',  'mdi:counter'],
    'lux':['lux','lux','lumen',  'mdi:weather-sunny'], 
    'temp':['temp', 'temp', 'C',  'mdi:thermometer'],    
    'humid':['humid', 'humid', '%',  'mdi:percent'] , 
    'soil':['soil', 'soil', '%',  'mdi:water-percent'], 
    'salt':['salt', 'salt', 'q',  'mdi:bottle-tonic'],
    'bat':['bat', 'bat', '%',  'mdi:battery'], 
    'rel':['rel', 'rel', ' ',  'mdi:alert-decagram'],
    }

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default='TIGO_HIgrow_Dendrobium'): cv.string, 
    vol.Optional(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)])
})

ATTRIBUTION = "LILYGO HI-Grow Sensor"

def setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the TIGO HIgrow sensor."""
    name = config.get(CONF_NAME)
    print("0")
#    print(name)
#    try:
#        HIgrow_data = open('dendrobium.json', 'r').read()
#    except ValueError as err:
#        _LOGGER.error("Received data error from TIGO_HIgrow: %s", err)
#        return
    def on_message(client, userdata, msg):
        print("4")
        m_decode=str(msg.payload.decode("utf-8","ignore"))
#        print("data Received type",type(m_decode))
#        print("data Received",m_decode)
#        print("Converting from Json to Object")
        m_in=json.loads(m_decode)
#        print(type(m_in))
        Temperatur =  m_in["temp"]["temp"], "C"
        print("broker 1 temp = ", Temperatur)
#       print("broker 1 soil = ",m_in["soil"]["soil"],  "%")
        print("5")
        HIgrow_data=m_decode
#        print("HIgrow_data 0")
#        print(HIgrow_data)
        dev = []
        print("6")
        for HIgrow in config[CONF_MONITORED_CONDITIONS]:
            convert_units = SENSOR_TYPES[HIgrow][2]
            sensor = name + '_' + SENSOR_TYPES[HIgrow][0]
            dev.append(TIGO_HIgrow(HIgrow_data, name, sensor, HIgrow,  convert_units))
            print("7a") 
        print("7")    
        async_add_entities(dev, True)




    brokers_out={"broker1":"192.168.1.35"}
    topic = name
    client=mqtt.Client(name)
    client.username_pw_set("mqtt", "ttqm")
    print("1")
#    HIgrow_data=str(msg.payload.decode("utf-8","ignore"))
#    print("Connecting to broker ",brokers_out["broker1"])
    client.connect(brokers_out["broker1"])
#    print("after client.connect")
    print("2")
#    client.loop_start()
    print("3")
    client.subscribe(topic)
    client.loop_start()
    client.on_message=on_message
    print("8")
    
    time.sleep(10)
  #  client.loop_stop()
  #  client.disconnect()




class TIGO_HIgrow(Entity):
    """Representation of a Sensor."""
    def __init__( self, HIgrow_data,  sensor, name, HIgrow,  convert_units):
        """Initialize the sensor."""
#        _LOGGER.debug("Init self ")
        self._name = name
        self._sensor = sensor
        self._HIgrow = HIgrow
        self._convert_units = SENSOR_TYPES[HIgrow][3]
        self._units = convert_units
        self._json_key = SENSOR_TYPES[HIgrow][0]
        self._icon = SENSOR_TYPES[HIgrow][3]
        self._data = json.loads(HIgrow_data) 
        self._state = None
        
        print("9")
#        self._rain_today = 0.00

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self._convert_units:
            return self._units
        else:
            return self._unit

    async def async_update(self, utcnow=None):
#    def update_state(self):
        """Get the latest data from Tgrow sensor and update the states."""
        #with open('dendrobium.json', 'r') as HIgrow_json:
#        print("Device: {}".format(self._HIgrow))
        print("10")
#        self._data = json.loads(self._data)
#        print("Data: ",  self._data)
        if self._data and (self._json_key in self._data):
            state = self._data[self._json_key][self._json_key]
            self._state = str(state)
#            print("state ",  state)
#        if self._json_key == 'time' or self._json_key == 'date' or self._json_key == 'dendrobium':
#            self._state = str(state)
#        elif self._json_key == 'bat':
#            state = float(state)
#            self._state = '{:_.3f}'.format(state).replace('.', ',').replace('_', '.')
#        else:
#            state = float(state)
#            self._state = '{:_.1f}'.format(state).replace('.', ',').replace('_', '.')