import os
import json

import paho.mqtt.client as mqtt

from mqttstatus.loop import TimerLoop
from mqttstatus.data import SystemData
from mqttstatus.log import logger


class MQTTAgent():

    def __init__(self,
                 host: str,
                 port: int,
                 username: str,
                 password: str,
                 prefix: str,
                 topic: str,
                 interval: int = 5):
        self.host = host
        self.port = port
        self.prefix = prefix
        self.topic = topic
        self.interval = interval
        self.data = SystemData()

        self.client = mqtt.Client()
        self.client.username_pw_set(username, password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.will_set(self.relative_topic("state"), "OFF")

    def run(self):
        self.client.connect(self.host, self.port, 60)
        self.update_loop = TimerLoop(self.interval, self.publish_update)
        self.update_loop.start()
        self.client.loop_forever()

    def stop(self):
        """
        Called when application is exiting to notify and gracefully end all threads
        """
        self.update_loop.cancel()
        self.publish_down()
        self.client.disconnect()

    def subscribe(self, topic_suffix: str):
        self.client.subscribe(self.relative_topic(topic_suffix))

    def publish(self, topic_suffix: str, payload: str, qos: int = 0, retain: bool = False):
        self.client.publish(self.relative_topic(topic_suffix),
                            payload,
                            qos,
                            retain)

    def relative_topic(self, suffix):
        """
        Convenience method to combine the prefix, topic, and provided suffix
        """
        return self.prefix+"/"+self.topic+"/"+suffix

    def on_connect(self, _client, _userdata, _flags, _rc):
        """
        Called after mqtt client connects to broker
        """
        logger.info("Connected to mqtt broker")
        self.subscribe("cmd/#")

    def on_message(self, _client, _userdata, msg):
        """
        Called after mqtt client receives a message it's subscribed to
        """
        if msg.topic == self.relative_topic("cmd/power") and msg.payload == bytes("OFF", "utf-8"):
            os.system('systemctl poweroff')
        else:
            logger.error("Unknown command: ", msg.topic, str(msg.payload))

    def publish_update(self):
        """
        Builds and sends updated status message to mqtt
        """
        self.publish("state", "ON")
        self.publish('data', json.dumps(self.data.get()))

    def publish_down(self):
        """
        Informs MQTT that this system state is OFF
        """
        self.publish('data', json.dumps(self.data.get()), 0, True)
        self.publish("state", "OFF")
