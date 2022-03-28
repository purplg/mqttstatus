import datetime
import os
import json
import subprocess
import psutil

import paho.mqtt.client as mqtt

from mqttstatus.loop import TimerLoop


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
        self.data = {}

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
        print("Connected to mqtt broker")
        self.subscribe("cmd/#")

    def on_message(self, _client, _userdata, msg):
        """
        Called after mqtt client receives a message it's subscribed to
        """
        if msg.topic == self.relative_topic("cmd/power") and msg.payload == bytes("OFF", "utf-8"):
            os.system('systemctl poweroff')
        else:
            print("Unknown command:", msg.topic, str(msg.payload))

    def publish_update(self):
        """
        Builds and sends updated status message to mqtt
        """
        self.get_timestamp()
        self.get_combined_cpu_usage()
        self.get_mem_usage()
        self.get_battery_percentage()
        self.publish("state", "ON")
        self.publish('data', json.dumps(self.data))

    def publish_down(self):
        """
        Informs MQTT that this system state is OFF
        """
        self.data['cpu'] = 0
        self.data['mem'] = 0
        self.publish('data', json.dumps(self.data), 0, True)
        self.publish("state", "OFF")

    def get_timestamp(self):
        """
        Populates 'last_updated' key in `data` current timestamp
        """
        self.data['last_updated'] = datetime.datetime.now().isoformat()

    def get_combined_cpu_usage(self):
        """
        Populates 'cpu' key in `data` with average cpu usage
        """
        self.data['cpu'] = psutil.cpu_percent()

    def get_mem_usage(self):
        """
        Populates 'mem' key in `data` with average cpu usage
        """
        self.data['mem'] = psutil.virtual_memory().percent

    def get_battery_percentage(self):
        """
        Populates 'bat#' key in `data` with each battery's current remaining
        percentage
        """
        cmd = 'acpi -b'
        p = subprocess.run(cmd.split(), shell=True, capture_output=True)
        bat_out, err = p.stdout.decode(), p.stderr.decode()
        # EXAMPLE OUTPUT:
        # Battery 0: Unknown, 99%
        # Battery 1: Discharging, 55%, 03:12:51 remaining

        if not err:
            bats = bat_out.split('\n')
            for i, bat in enumerate(bats):
                if len(bat) > 1:
                    self.data[f'bat{i}'] = bat.split(', ')[1][0:-1]
