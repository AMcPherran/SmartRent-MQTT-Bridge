import typing
import json
import asyncio
import mitmproxy.websocket
import paho.mqtt.client as mqtt
import ssl
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

#######################################################


MQTT_HOST = os.environ.get('MQTT_HOST')    
MQTT_PORT = int(os.environ.get('MQTT_PORT'))
MQTT_USER = os.environ.get('MQTT_USER')    
MQTT_PASS = os.environ.get('MQTT_PASS')    
MQTT_TLS  = bool(os.environ.get('MQTT_TLS'))
MQTT_TOPIC_PREFIX = os.environ.get('MQTT_TOPIC_PREFIX')    

devices = {
#  deviceId: ["friendly name", "device_mqtt_topic", "device type"]
    31411: ["Bedroom Thermostat", "bedroom_thermostat", "thermostat"],
    31406: ["Office Thermostat", "office_thermostat", "thermostat"],
    31399: ["Living Room Thermostat", "living_room_thermostat", "thermostat"],
    31389: ["Front Door Lock", "front_door_lock", "lock"]
}


#######################################################
topics = {}
ws_message = ''
def on_mqtt_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with result code "+str(rc))

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, password=MQTT_PASS)
if MQTT_TLS is True:
    mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
    mqtt_client.tls_insecure_set(not MQTT_TLS)
mqtt_client.on_connect = on_mqtt_connect


class SmartRentBridge:

    def __init__(self):
        mqtt_client.on_message = self.on_mqtt_message
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
        mqtt_client.loop_start()
        for key, value in devices.items():
            topics[value[1]] = [key, value[2]]
            if value[2] == "thermostat":
                mqtt_client.subscribe(MQTT_TOPIC_PREFIX+'/'+value[1]+'/target/set')
                mqtt_client.subscribe(MQTT_TOPIC_PREFIX+'/'+value[1]+'/mode/set')
            if value[2] == "lock":
                mqtt_client.subscribe(MQTT_TOPIC_PREFIX+'/'+value[1]+'/set')

    async def inject(self, flow: mitmproxy.websocket.WebSocketFlow):
        global ws_message
        while not flow.ended and not flow.error:
            if len(ws_message) > 0 :
               flow.inject_message(flow.server_conn, str(ws_message))
               print(ws_message)
               ws_message = ''

            await asyncio.sleep(2)

    def on_mqtt_message(self, client, userdata, msg):
        global ws_message
        topic = msg.topic.split('/')
        device_id = str(topics[topic[1]][0])
        device_type = topics[topic[1]][1]
        command = topic[2]
        value = msg.payload.decode().lower()
        # Handle Thermostat Commands
        if device_type == "thermostat":
            if command == "mode":
                ws_message = '["6","69","devices:'+device_id+'","update_attributes",{"device_id":"'+device_id+'","attributes":[{"name":"mode","value":"'+value+'"},{"name":"heating_setpoint","value":"68"}]}]'
            if command == "target":
                ws_message = '["6","69","devices:'+device_id+'","update_attributes",{"device_id":"'+device_id+'","attributes":[{"name":"mode","value":"heat"},{"name":"heating_setpoint","value":"'+value+'"}]}]'
        # Handle Lock Commands
        if device_type == "lock":
           ws_message = '["null","null","devices:'+device_id+'","update_attributes",{"device_id":"'+device_id+'","attributes":[{"name":"locked","value":"'+value+'"}]}]'


    #####
    def websocket_start(self, flow):
        asyncio.get_event_loop().create_task(self.inject(flow))

    def websocket_message(self, flow: mitmproxy.websocket.WebSocketFlow):
        message = flow.messages[-1]
        self.parse_message(message.content)

    def parse_message(self, message):
        message_json = json.loads(message)
        msg_type = message_json[3]
        msg_data = message_json[4]
        if msg_type == "attribute_state":
            attribute = msg_data['attribute']
            device_id = msg_data['device_id']
            value = msg_data['value']
            # Thermostat Setpoint
            if attribute == "heating_setpoint":
                mqtt_client.publish(MQTT_TOPIC_PREFIX+'/'+devices[device_id][1]+'/target', value)
            if attribute == "current_temp":
                mqtt_client.publish(MQTT_TOPIC_PREFIX+'/'+devices[device_id][1]+'/current', value)
            # Thermostat Mode
            if attribute == "mode":
                mqtt_client.publish(MQTT_TOPIC_PREFIX+'/'+devices[device_id][1]+'/mode', value)

            ######################
            # Lock State
            if attribute == "locked":
                mqtt_client.publish(MQTT_TOPIC_PREFIX+'/'+devices[device_id][1]+'/status', value)
                print(MQTT_TOPIC_PREFIX+'/'+devices[device_id][1]+'/status')
            if attribute == "notifications":
                mqtt_client.publish(MQTT_TOPIC_PREFIX+'/'+devices[device_id][1]+'/detail', value)
                print(MQTT_TOPIC_PREFIX+'/'+devices[device_id][1]+'/detail')
        print(message)
        return



addons = [SmartRentBridge()]
