"""Support for MQTT message handling."""
import asyncio
import datetime as dt
import logging
from itertools import groupby
from operator import attrgetter
from typing import Callable, List, Optional, Union

import attr

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 1883
DEFAULT_KEEPALIVE = 60
PROTOCOL_311 = "3.1.1"
DEFAULT_PROTOCOL = PROTOCOL_311
MQTT_CONNECTED = "blitzortung_mqtt_connected"
MQTT_DISCONNECTED = "blitzortung_mqtt_disconnected"


MAX_RECONNECT_WAIT = 300  # seconds


def _raise_on_error(result_code: int) -> None:
    """Raise error if error result."""
    # pylint: disable=import-outside-toplevel
    import paho.mqtt.client as mqtt

    if result_code != 0:
        raise HomeAssistantError(
            f"Error talking to MQTT: {mqtt.error_string(result_code)}"
        )


def _match_topic(subscription: str, topic: str) -> bool:
    """Test if topic matches subscription."""
    # pylint: disable=import-outside-toplevel
    from paho.mqtt.matcher import MQTTMatcher

    matcher = MQTTMatcher()
    matcher[subscription] = True
    try:
        next(matcher.iter_match(topic))
        return True
    except StopIteration:
        return False


PublishPayloadType = Union[str, bytes, int, float, None]


@attr.s(slots=True, frozen=True)
class Message:
    """MQTT Message."""

    topic = attr.ib(type=str)
    payload = attr.ib(type=PublishPayloadType)
    qos = attr.ib(type=int)
    retain = attr.ib(type=bool)
    subscribed_topic = attr.ib(type=str, default=None)
    timestamp = attr.ib(type=dt.datetime, default=None)


MessageCallbackType = Callable[[Message], None]


@attr.s(slots=True, frozen=True)
class Subscription:
    """Class to hold data about an active subscription."""

    topic = attr.ib(type=str)
    callback = attr.ib(type=MessageCallbackType)
    qos = attr.ib(type=int, default=0)
    encoding = attr.ib(type=str, default="utf-8")


SubscribePayloadType = Union[str, bytes]  # Only bytes if encoding is None


class MQTT:
    """Home Assistant MQTT client."""

    def __init__(
        self,
        hass: HomeAssistantType,
        host,
        port=DEFAULT_PORT,
        keepalive=DEFAULT_KEEPALIVE,
    ) -> None:
        """Initialize Home Assistant MQTT client."""
        # We don't import on the top because some integrations
        # should be able to optionally rely on MQTT.
        import paho.mqtt.client as mqtt  # pylint: disable=import-outside-toplevel

        self.hass = hass
        self.host = host
        self.port = port
        self.keepalive = keepalive
        self.subscriptions: List[Subscription] = []
        self.connected = False
        self._mqttc: mqtt.Client = None
        self._paho_lock = asyncio.Lock()

        self.init_client()

    def init_client(self):
        """Initialize paho client."""
        # We don't import on the top because some integrations
        # should be able to optionally rely on MQTT.
        import paho.mqtt.client as mqtt  # pylint: disable=import-outside-toplevel

        proto = mqtt.MQTTv311
        self._mqttc = mqtt.Client(protocol=proto)

        self._mqttc.on_connect = self._mqtt_on_connect
        self._mqttc.on_disconnect = self._mqtt_on_disconnect
        self._mqttc.on_message = self._mqtt_on_message

    async def async_publish(
        self, topic: str, payload: PublishPayloadType, qos: int, retain: bool
    ) -> None:
        """Publish a MQTT message."""
        async with self._paho_lock:
            _LOGGER.debug("Transmitting message on %s: %s", topic, payload)
            await self.hass.async_add_executor_job(
                self._mqttc.publish, topic, payload, qos, retain
            )

    async def async_connect(self) -> str:
        """Connect to the host. Does not process messages yet."""
        # pylint: disable=import-outside-toplevel
        import paho.mqtt.client as mqtt

        result: int = None
        try:
            result = await self.hass.async_add_executor_job(
                self._mqttc.connect, self.host, self.port, self.keepalive,
            )
        except OSError as err:
            _LOGGER.error("Failed to connect to MQTT server due to exception: %s", err)

        if result is not None and result != 0:
            _LOGGER.error(
                "Failed to connect to MQTT server: %s", mqtt.error_string(result)
            )

        self._mqttc.loop_start()

    async def async_disconnect(self):
        """Stop the MQTT client."""

        def stop():
            """Stop the MQTT client."""
            self._mqttc.disconnect()
            self._mqttc.loop_stop()

        await self.hass.async_add_executor_job(stop)

    async def async_subscribe(
        self,
        topic: str,
        msg_callback,
        qos: int,
        encoding: Optional[str] = None,
    ) -> Callable[[], None]:
        """Set up a subscription to a topic with the provided qos.

        This method is a coroutine.
        """
        if not isinstance(topic, str):
            raise HomeAssistantError("Topic needs to be a string!")

        subscription = Subscription(topic, msg_callback, qos, encoding)
        self.subscriptions.append(subscription)

        # Only subscribe if currently connected.
        if self.connected:
            await self._async_perform_subscription(topic, qos)

        @callback
        def async_remove() -> None:
            """Remove subscription."""
            if subscription not in self.subscriptions:
                raise HomeAssistantError("Can't remove subscription twice")
            self.subscriptions.remove(subscription)

            if any(other.topic == topic for other in self.subscriptions):
                # Other subscriptions on topic remaining - don't unsubscribe.
                return

            # Only unsubscribe if currently connected.
            if self.connected:
                self.hass.async_create_task(self._async_unsubscribe(topic))

        return async_remove

    async def _async_unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic.

        This method is a coroutine.
        """
        _LOGGER.debug("Unsubscribing from %s", topic)
        async with self._paho_lock:
            result: int = None
            result, _ = await self.hass.async_add_executor_job(
                self._mqttc.unsubscribe, topic
            )
            _raise_on_error(result)

    async def _async_perform_subscription(self, topic: str, qos: int) -> None:
        """Perform a paho-mqtt subscription."""
        _LOGGER.debug("Subscribing to %s", topic)

        async with self._paho_lock:
            result: int = None
            result, _ = await self.hass.async_add_executor_job(
                self._mqttc.subscribe, topic, qos
            )
            _raise_on_error(result)

    def _mqtt_on_connect(self, _mqttc, _userdata, _flags, result_code: int) -> None:
        """On connect callback.

        Resubscribe to all topics we were subscribed to and publish birth
        message.
        """
        # pylint: disable=import-outside-toplevel
        import paho.mqtt.client as mqtt

        if result_code != mqtt.CONNACK_ACCEPTED:
            _LOGGER.error(
                "Unable to connect to the MQTT broker: %s",
                mqtt.connack_string(result_code),
            )
            return

        self.connected = True
        dispatcher_send(self.hass, MQTT_CONNECTED)
        _LOGGER.info(
            "Connected to MQTT server %s:%s (%s)", self.host, self.port, result_code,
        )

        # Group subscriptions to only re-subscribe once for each topic.
        keyfunc = attrgetter("topic")
        for topic, subs in groupby(sorted(self.subscriptions, key=keyfunc), keyfunc):
            # Re-subscribe with the highest requested qos
            max_qos = max(subscription.qos for subscription in subs)
            self.hass.add_job(self._async_perform_subscription, topic, max_qos)

    def _mqtt_on_message(self, _mqttc, _userdata, msg) -> None:
        """Message received callback."""
        self.hass.add_job(self._mqtt_handle_message, msg)

    @callback
    def _mqtt_handle_message(self, msg) -> None:
        _LOGGER.debug(
            "Received message on %s%s: %s",
            msg.topic,
            " (retained)" if msg.retain else "",
            msg.payload,
        )
        timestamp = dt_util.utcnow()

        for subscription in self.subscriptions:
            if not _match_topic(subscription.topic, msg.topic):
                continue

            payload: SubscribePayloadType = msg.payload
            if subscription.encoding is not None:
                try:
                    payload = msg.payload.decode(subscription.encoding)
                except (AttributeError, UnicodeDecodeError):
                    _LOGGER.warning(
                        "Can't decode payload %s on %s with encoding %s (for %s)",
                        msg.payload,
                        msg.topic,
                        subscription.encoding,
                        subscription.callback,
                    )
                    continue

            self.hass.async_run_job(
                subscription.callback,
                Message(
                    msg.topic,
                    payload,
                    msg.qos,
                    msg.retain,
                    subscription.topic,
                    timestamp,
                ),
            )

    def _mqtt_on_disconnect(self, _mqttc, _userdata, result_code: int) -> None:
        """Disconnected callback."""
        self.connected = False
        dispatcher_send(self.hass, MQTT_DISCONNECTED)
        _LOGGER.info(
            "Disconnected from MQTT server %s:%s (%s)",
            self.host,
            self.port,
            result_code,
        )
