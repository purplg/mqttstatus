#!/usr/bin/python3
import sys
import os
import signal
import threading
import subprocess
import json
import datetime
import yaml
import psutil
from ewmh import EWMH
from Xlib import error
import paho.mqtt.client as mqtt

try:
    ewmh = EWMH()
except error.DisplayNameError:
    ewmh = None

data = {}

# -------------------------------------------------
# CONFIGURATION
def required(conf, key):
    """Try to get key from yaml file. Exit if fail"""
    try:
        return conf[key]
    except KeyError:
        print('Config: Missing required key:', key)
        sys.exit(0)

def optional(conf, key, default):
    """Try to get key from yaml file. Returns default if fail"""
    try:
        return conf[key]
    except KeyError:
        print('Config: Using default value for missing key:', key)
        return default

try:
    with open(r'mqttstatus.yaml') as file:
        yaml_file = yaml.load(file, Loader=yaml.FullLoader)
        PREFIX = required(yaml_file, 'prefix')
        TOPIC = required(yaml_file, 'topic')
        USERNAME = required(yaml_file, 'username')
        PASSWORD = required(yaml_file, 'password')
        INTERVAL = optional(yaml_file, 'interval', 60)
except yaml.scanner.ScannerError:
    print('Invalid config format')
    sys.exit(0)

# -------------------------------------------------
# MQTT
def relative_topic(suffix):
    """Convenience method to combine the prefix, topic, and provided suffix"""
    return PREFIX+"/"+TOPIC+"/"+suffix

def on_connect(_client, _userdata, _flags, _rc):
    """Called after mqtt client connects to broker"""
    print("Connected to mqtt broker")
    CLIENT.subscribe(relative_topic("cmd/#"))

def on_message(_client, _userdata, msg):
    """Called after mqtt client receives a message it's subscribed to"""
    if msg.topic == relative_topic("cmd/power") and msg.payload == bytes("OFF", "utf-8"):
        os.system('systemctl poweroff')
    else:
        print("Unknown command:", msg.topic, str(msg.payload))

def publish_update():
    """Builds and sends updated status message to mqtt"""
    print("publish_update")
    get_timestamp()
    get_running_game()
    get_combined_cpu_usage()
    get_individual_cpu_usage()
    get_mem_usage()
    get_battery_percentage()
    CLIENT.publish(relative_topic("state"), "ON")
    CLIENT.publish(relative_topic('data'), json.dumps(data))

def publish_down():
    """Informs MQTT that this system state is OFF"""
    CLIENT.publish(relative_topic("state"), "OFF")

CLIENT = mqtt.Client()
CLIENT.username_pw_set(USERNAME, PASSWORD)
CLIENT.on_connect = on_connect
CLIENT.on_message = on_message
CLIENT.will_set(relative_topic("state"), "OFF")
CLIENT.connect("10.0.2.3", 1883, 60)

# -------------------------------------------------
# LOOP
class TimerLoop():
    """Calls the `handler` function ever `interval` seconds"""

    def __init__(self, interval, handler):
        self.interval = interval
        self.handler = handler
        self.thread = threading.Timer(self.interval, self._tick)

    def _tick(self):
        self.handler()
        self.thread = threading.Timer(self.interval, self._tick)
        self.thread.start()

    def start(self):
        """Start the loop"""
        self.thread.start()

    def cancel(self):
        """Cancel the loop"""
        self.thread.cancel()

LOOP = TimerLoop(INTERVAL, publish_update)

# -------------------------------------------------
# SYSTEM DATA TO BE PUBLISHED
def get_timestamp():
    """Populates 'last_updated' key in `data` current timestamp"""
    data['last_updated'] = datetime.datetime.now().isoformat()
def get_combined_cpu_usage():
    """Populates 'cpu' key in `data` with average cpu usage"""
    data['cpu'] = psutil.cpu_percent()
def get_individual_cpu_usage():
    """Populates 'cpu#' keys in `data` with each logical cpu's usage"""
    for i, cpu in enumerate(psutil.cpu_percent(None, True)):
        data[f'cpu{i}'] = cpu

def get_mem_usage():
    """Populates 'mem' key in `data` with average cpu usage"""
    data['mem'] = psutil.virtual_memory().percent
def get_battery_percentage():
    """Populates 'bat#' key in `data` with each battery's current remaining percentage"""
    cmd = 'acpi -b'
    p = subprocess.run(cmd.split(), shell=True, capture_output=True)
    bat_out, err = p.stdout.decode(), p.stderr.decode()
    #EXAMPLE OUTPUT:
    #Battery 0: Unknown, 99%
    #Battery 1: Discharging, 55%, 03:12:51 remaining

    if not err:
        bats = bat_out.split('\n')
        for i, bat in enumerate(bats):
            if len(bat) > 1:
                data[f'bat{i}'] = bat.split(', ')[1][0:-1]

def get_running_game():
    """Populates 'game' key in `data` with the first fullscreen X11 client"""
    if ewmh:
        for win in ewmh.getClientList():
            name = str(ewmh.getWmName(win), 'utf-8')
            state = ewmh.getWmState(win, True)
            if len(state) > 0 and state[0] == '_NET_WM_STATE_FULLSCREEN':
                data['game'] = name
                break
        data['game'] = "None"


# -------------------------------------------------
# SHUTDOWN
def exit_gracefully(_signum, _frame):
    """Called when application is exiting to notify and gracefully end all threads"""
    publish_down()
    CLIENT.disconnect()
    LOOP.cancel()

publish_update()

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

LOOP.start()

CLIENT.loop_forever()
