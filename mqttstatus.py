#!/usr/bin/python3
import sched
import sys
import os
import signal
import threading
import paho.mqtt.client as mqtt
import yaml
import json
import psutil
from time import sleep
import datetime
from ewmh import EWMH
from Xlib import error

try:
    ewmh = EWMH()
except error.DisplayNameError:
    ewmh = None

UPDATE_INTERVAL = 60

prefix = None
topic = None
username = None
password = None
client = None
aliveTimer = None

data = {}

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

def aliveTimerHandler():
    publishUpdate()
    global aliveTimer
    aliveTimer = threading.Timer(UPDATE_INTERVAL, aliveTimerHandler)
    aliveTimer.start()

def publishUpdate():
    getTimestamp()
    getRunningGame()
    getAverageCpuUsage()
    getCpuUsage()
    getMemUsage()
    global client
    client.publish(relativetopic("state"), "ON")
    client.publish(relativetopic('data'), json.dumps(data))

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
    publishUpdate()

def exit_gracefully(signum, frame):
    publishDown()
    client.disconnect()
    aliveTimer.cancel()
    aliveTimer.join()

def getTimestamp():
    data['last_updated'] = datetime.datetime.now().isoformat()
def getAverageCpuUsage():
    data['cpu'] = psutil.cpu_percent()
def getCpuUsage():
    for i, cpu in enumerate(psutil.cpu_percent(None, True)):
        data[f'cpu{i}'] = cpu

def getMemUsage():
    data['mem'] = psutil.virtual_memory().percent

def getRunningGame():
    if ewmh:
        for win in ewmh.getClientList():
            name = str(ewmh.getWmName(win), 'utf-8')
            state = ewmh.getWmState(win, True)
            if len(state) > 0 and state[0] == '_NET_WM_STATE_FULLSCREEN':
                data['game'] = name
                break
        data['game'] = "None"


config()
startMqtt()

aliveTimer = threading.Timer(UPDATE_INTERVAL, aliveTimerHandler)
aliveTimer.start()

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

client.loop_forever()
