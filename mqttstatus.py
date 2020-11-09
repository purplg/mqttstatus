#!/usr/bin/python3

import sched, sys, os, signal, threading
import paho.mqtt.client as mqtt
from time import sleep
import yaml

UPDATE_INTERVAL = 60

prefix = None
topic = None
username = None
password = None
client = None

def config():
    try:
        with open(r'mqttstatus.yaml') as file:
            global prefix, topic, username, password
            l = yaml.load(file, Loader=yaml.FullLoader)
            try:
                prefix = l['prefix']
            except KeyError:
                print('Config: Missing prefix')
                exit(0)
            try:
                topic = l['topic']
            except KeyError:
                print('Config: Missing topic')
                exit(0)
            try:
                username = l['username']
            except KeyError:
                print('Config: Missing username')
                exit(0)
            try:
                password = l['password']
            except KeyError:
                print('Config: Missing password')
                exit(0)
    except yaml.scanner.ScannerError:
        print('Invalid config')
        exit(0)

def relativetopic(suffix):
    return prefix+"/"+topic+"/"+suffix

def on_connect(client, userdata, flags, rc):
    print("connected with result code "+str(rc))
    client.subscribe(relativetopic("cmd/#"))

def on_message(client, userdata, msg):
    if msg.topic == relativetopic("cmd/power") and msg.payload == bytes("OFF", "utf-8"):
        os.system('systemctl poweroff')
    else:
        print("Unknown command:", msg.topic, str(msg.payload))

def publishUp():
    global client
    client.publish(relativetopic("state"), "ON")

def publishDown():
    global client
    client.publish(relativetopic("state"), "OFF")

def startMqtt():
    global client
    client = mqtt.Client()
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.will_set(relativetopic("state"), "OFF")
    client.connect("10.0.2.3", 1883, 60)
    publishUp()
    client.loop_start()

def aliveTimerHandler():
    publishUp()
    aliveTimer = threading.Timer(UPDATE_INTERVAL, aliveTimerHandler)
    aliveTimer.start()

config()
startMqtt()
aliveTimer = threading.Timer(UPDATE_INTERVAL, aliveTimerHandler)
aliveTimer.start()

try:
    while True:
        sleep(10000)
except KeyboardInterrupt:
    exit(0)
finally:
    aliveTimer.cancel()
    publishDown()
