import json

import paho.mqtt.client as mqtt

from mqttstatus.loop import TimerLoop
from mqttstatus.data import SystemData
from mqttstatus.log import logger
from mqttstatus import modules


class MQTTAgent(mqtt.Client):
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        prefix: str,
        topic: str,
        interval: int = 5,
    ):
        super().__init__()
        self.host = host
        self.port = port
        self.prefix = prefix
        self.topic = topic
        self.interval = interval
        self.data = SystemData()

        self.update_loop = TimerLoop(self.interval, self.publish_update)
        self.username_pw_set(username, password)
        self.will_set(self.relative_topic("state"), "OFF")

        self.modules = [
            modules.Poweroff(),
            modules.Notify(),
        ]

        for module in self.modules:
            module.start()

    def run(self):
        self.connect(self.host, self.port, 60)
        self.update_loop.start()
        self.loop_forever()

    def stop(self):
        """
        Called when application is exiting to notify and gracefully end all threads
        """
        self.update_loop.cancel()
        self.publish_down()
        self.disconnect()

    def subscribe(self, topic_suffix):
        super().subscribe(self.relative_topic(topic_suffix))

    def publish(self, topic_suffix, payload, qos=0, retain=False):
        super().publish(
            topic=self.relative_topic(topic_suffix),
            payload=payload,
            qos=qos,
            retain=retain,
        )

    def relative_topic(self, suffix):
        """
        Convenience method to combine the prefix, topic, and provided suffix
        """
        return self.prefix + "/" + self.topic + "/" + suffix

    def on_connect(self, _client, _userdata, _flags, _rc):
        """
        Called after mqtt client connects to broker
        """
        logger.info("Connected to mqtt broker")
        self.subscribe("cmd/#")

    def on_message(self, client, userdata, msg):
        """
        Called after mqtt client receives a message it's subscribed to
        """
        cmd = msg.topic.removeprefix(self.relative_topic("cmd/"))
        payload = msg.payload.decode("utf-8")

        for module in self.modules:
            module.on_mqtt(cmd, payload)

    def publish_update(self):
        """
        Builds and sends updated status message to mqtt
        """
        self.publish("state", "ON")
        self.publish("data", json.dumps(self.data.get()))

    def publish_down(self):
        """
        Informs MQTT that this system state is OFF
        """
        self.publish("data", json.dumps(self.data.get()), 0, True)
        self.publish("state", "OFF")
