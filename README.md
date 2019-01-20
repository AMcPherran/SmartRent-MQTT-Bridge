This software is provided for free to do whatever you want with, I make no guarantees about it but it has worked well for me for the past few months.
I had SmartRent devices installed in my apartment but SmartRent does not provide any sort of API for residents to use, so I made my own solution to integrate their devices with [Home Assistant](https://www.home-assistant.io/). It's pretty hacky, but it works!

## How it Works:
When the container starts, a Chrome is launched as a Selenium driver and navigates to the SmartRent login page, logs you in, then navigates to the home control page.
Chrome is configured to proxy the connection through [mitmproxy](https://mitmproxy.org/) with the `smartrent-bridge.py` script set to manipulate the WebSocket connection. 
`smartrent-bridge.py` will translate MQTT publications to WebSocket messages and vice-versa.

# How to use it: 
The easiest way to run this is with [Docker](https://docs.docker.com/install/):
`docker build . -t smartrent-mqtt-bridge`
`docker run --env-file smartrent.env -it smartrent-mqtt-bridge`

## Configure your Devices:
You will likely need to edit the `devices` variable in `smartrent-bridge.py` to make it match the devices and Device IDs in your apartment. I found my device IDs by watching the messages in the logs as I interacted with each device (either physically or via the SmartRent app/web)

    devices = {
    #   devId: ["friendly name", "device_mqtt_topic", "device type"]
        31411: ["Bedroom Thermostat", "bedroom_thermostat", "thermostat"],
        31406: ["Office Thermostat", "office_thermostat", "thermostat"],
        31399: ["Living Room Thermostat", "living_room_thermostat", "thermostat"],
        31389: ["Front Door Lock", "front_door_lock", "lock"]
    }
 

## Set these Environment Variables in `smartrent.env`: 
| Variable         | Example          | Purpose  |
| ---------------- |:----------------:|--------|
|SMARTRENT_EMAIL   | user@example.com | Used to automatically log into your SmartRent account with Selenium
|SMARTRENT_PASSWORD| aS$ecureP4ssw0rd | ^
|MQTT_HOST         | mqtt.example.com | IP/Hostname of your MQTT Broker
|MQTT_PORT         | 8883             | MQTT broker defaults are 1883 and 8883 for TLS
|MQTT_TLS          | True             | Whether communication with MQTT Broker should be encrypted
|MQTT_USER         | mqtt_user        | MQTT Username
|MQTT_PASS         | example_pass     | MQTT Password
|MQTT_TOPIC_PREFIX | smartrent        | Prefix for all MQTT topics

## MQTT Topics
`<device_mqtt_topic>` is determined by the `devices` variable configuration.
#### Thermostat Topics
| MQTT Topic                                       |       Purpose                             |   Values      |
| ------------------------------------------------ |:------------------------------------------|:-------------:|
|<MQTT_TOPIC_PREFIX>/<device_mqtt_topic>/target    | The current target temperature            | Integer       |
|<MQTT_TOPIC_PREFIX>/<device_mqtt_topic>/target/set| Set the the desired target temperature    | Integer       |
|<MQTT_TOPIC_PREFIX>/<device_mqtt_topic>/current   | The current actual temperature            | Integer       |
|<MQTT_TOPIC_PREFIX>/<device_mqtt_topic>/mode      | The curent operation mode                 | "off","heat"  |
|<MQTT_TOPIC_PREFIX>/<device_mqtt_topic>/mode/set  | Set the desired operation mode            | "off","heat"  |
#### Lock Topics
| MQTT Topic                                     |       Purpose                          |   Values              |
| ---------------------------------------------- |:---------------------------------------|:---------------------:|
|<MQTT_TOPIC_PREFIX>/<device_mqtt_topic>/status  | The current state of the lock          | "locked","unlocked"   |
|<MQTT_TOPIC_PREFIX>/<device_mqtt_topic>/set     | Set whether the door should be lock    | "true"                |
|<MQTT_TOPIC_PREFIX>/<device_mqtt_topic>/detail  | Details about the last lock interaction| String                |

# More on SmartRent's System
## Websocket Message Formats
A list of the important WebSocket messages exchanged between the web client and SmartRent's service can be found [here (WIP)](https://github.com/AMcPherran/SmartRent-MQTT-Bridge/blob/master/Message-Formats.md)
## The Hub
The hub provided by SmartRent is a device made by Zipato called the [ZipaMicro](https://www.zipato.com/product/zipamicro).
This hub connects to all of the devices over [Z-Wave](https://www.z-wave.com/) local RF, and connects them to ZipaMicro's cloud-services, which then are called by SmartRent's service. The hub comes with a USB LTE dongle to keep it connected if you decide not to connect it to your LAN. 

On the LAN interface, the hub has a Dropbear SSH server listening on port 22, and a REST API on port 8080. I'm not sure what ports are open over the LTE connection.

![Hub Exterior](https://github.com/AMcPherran/SmartRent-MQTT-Bridge/raw/master/images/devices/smartrent-hub-exterior.jpg)
![Hub Interior](https://github.com/AMcPherran/SmartRent-MQTT-Bridge/raw/master/images/devices/smartrent-hub-internal.jpg)
![Hub Ports](https://github.com/AMcPherran/SmartRent-MQTT-Bridge/raw/master/images/devices/smartrent-hub-ports.jpg)
![Hub Bottom](https://github.com/AMcPherran/SmartRent-MQTT-Bridge/raw/master/images/devices/smartrent-hub-sticker.jpg)

## The Lock
The lock that was installed on my door is made by Yale. It has a touch-panel keypad and no physical key. 
The lock reports the USER_ID associated with the PIN used to unlock the door, the current state of the lock, and the method used to lock/unlock the door (keypad, network, thumbturn, inside/outside). From this it is easy to infer the arrival/departure times of residents. 

![Lock Outside](https://github.com/AMcPherran/SmartRent-MQTT-Bridge/raw/master/images/devices/yale-lock-outside.jpg)
![Lock Inside](https://github.com/AMcPherran/SmartRent-MQTT-Bridge/raw/master/images/devices/yale-lock-inside.jpg)
