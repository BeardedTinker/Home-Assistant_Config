import homeassistant.loader as loader
import os
from distutils.dir_util import copy_tree
from datetime import datetime

DOMAIN = 'zigbee2mqtt_networkmap'

DEPENDENCIES = ['mqtt']

CONF_TOPIC = 'topic'
DEFAULT_TOPIC = 'zigbee2mqtt'


async def async_setup(hass, config):
    fromDirectory = hass.config.path('custom_components', 'zigbee2mqtt_networkmap', 'www')
    toDirectory = hass.config.path('www', 'community', 'zigbee2mqtt_networkmap')

    if os.path.exists(toDirectory) and os.path.isdir(toDirectory):
        print(toDirectory)

    copy_tree(fromDirectory, toDirectory)

    """Set up the zigbee2mqtt_networkmap component."""
    mqtt = hass.components.mqtt
    topic = config[DOMAIN].get(CONF_TOPIC, DEFAULT_TOPIC)
    entity_id = 'zigbee2mqtt_networkmap.map_last_update'

    async def handle_webhook(hass, webhook_id, request):
        """Handle webhook callback."""
        mqtt.async_publish(topic+'/bridge/networkmap', 'graphviz')
    # Register the Webhook
    webhook_id = hass.components.webhook.async_generate_id()
    hass.components.webhook.async_register(
        DOMAIN, 'zigbee2mqtt_networkmap webhook', webhook_id, handle_webhook)
    webhook_url = hass.components.webhook.async_generate_url(webhook_id)

    # Listener to be called when we receive a message.
    async def message_received(msg):
        """Handle new MQTT messages."""
        # Save Response as JS variable in source.js
        payload = msg.payload.replace('\n', ' ').replace(
            '\r', '').replace("'", r"\'")
        last_update = datetime.now()
        f = open(hass.config.path(
            'www', 'community', 'zigbee2mqtt_networkmap', 'source.js'), "w")
        f.write("var webhook = '"+webhook_url+"';\nvar last_update = new Date('" +
                last_update.strftime('%Y/%m/%d %H:%M:%S')+"');\nvar graph = \'"+payload+"\'")
        f.close()
        hass.states.async_set(entity_id, last_update)

    # Subscribe our listener to the networkmap topic.
    await mqtt.async_subscribe(topic+'/bridge/networkmap/graphviz', message_received)

    # Set the initial state.
    hass.states.async_set(entity_id, None)

    # Service to publish a message on MQTT.
    async def update_service(call):
        """Service to send a message."""
        mqtt.async_publish(topic+'/bridge/networkmap', 'graphviz')

    hass.services.async_register(DOMAIN, 'update', update_service)
    return True
