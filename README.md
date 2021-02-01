  <h4>
    <a href="https://github.com/BeardedTinker/Home-Assistant_Config/actions"><img src="https://img.shields.io/github/workflow/status/BeardedTinker/Home-Assistant_Config/Home%20Assistant%20CI?label=GitHub%20CI&style=plastic"/></a>
    <a href="https://travis-ci.com/BeardedTinker/Home-Assistant_Config"><img src="https://img.shields.io/travis/beardedtinker/home-assistant_config?label=Travis%20CI&style=plastic"/></a>
    <a href="https://github.com/BeardedTinker/Home-Assistant_Config/stargazers"><img src="https://img.shields.io/github/stars/BeardedTinker/Home-Assistant_Config.svg?style=plasticr"/></a>
    <a href="https://github.com/BeardedTinker/Home-Assistant_Config/commits/master"><img src="https://img.shields.io/github/last-commit/BeardedTinker/Home-Assistant_Config.svg?style=plasticr"/></a>
        <a href="https://github.com/BeardedTinker/Home-Assistant_Config/commits/master"><img src="https://img.shields.io/github/commit-activity/y/BeardedTinker/Home-Assistant_config?style=plastic"/></a>
    <a href="https://discord.gg/HkxDRN6"><img src="https://img.shields.io/discord/675020779955683328?label=Discord%20BeardedHome&logo=discord"/></a><br>


Each commit is verified automaticlly with <a href="https://travis-ci.com/github/BeardedTinker/Home-Assistant_Config">Travis CI</a>, but also with <a href="https://github.com/BeardedTinker/Home-Assistant_Config/actions">GitHub CI</a> - where it's tested against Latest, Dev and Beta release
  </h4>


# BeardedTinker's Home Assistant configuration

Here is a shot on making my Home Assistant configuration available.
All individual files should have comments inside and I'll try to add as much documentation as I can over time.


## Want to get more info?

You can follow my [YouTube channel](https://YouTube.com/BeardedTinker) for more information and video guides for various stuff that's included here. 

If you want to get in touch, you can always find me on Discord Server - [BeardedHome](https://discord.gg/HkxDRN6) 

Also, you can try and get in touch while I'm streaming. There should be at least 1 stream each month!


### Hardware

This system is running on Synology DS415+ with total of 8GB RAM inside.
Plugged in Synolgoy is cc2531 Zigbee USB stick with Zigbee2mqtt firmware from Koenkk version [20190608](https://github.com/Koenkk/Z-Stack-firmware/raw/master/coordinator/Z-Stack_Home_1.2/bin/default/CC2531_DEFAULT_20190608.zip)

From other devices I use, here is a list:
  - IKEA TRADFRI Gateway - NOT used anymore
  - IKEA TRADFRI wireless dimmer (ICTC-G-1) - NOT used anymore
  - IKEA TRADFRI remote control (E1524/E1810)
  - IKEA TRADFRI ON/OFF switch (E1743)
  - IKEA TRADFRI control outlet (E1603/E1702)
  - IKEA TRADFRI various bulbs of all sizes and shapes (LED1545G12, LED1623G12, LED1650R5, LED1536G5, LED1649C5, LED1736G9)
  - Xiaomi MiJia wireless switch [WXKG01LM](https://www.zigbee2mqtt.io/devices/WXKG01LM.html) - [AliExpress link](https://s.click.aliexpress.com/e/_dW7ZKDA)
  - Xiaomi MiJia temperature & humidity sensor [WSDCGQ01LM](https://www.zigbee2mqtt.io/devices/WSDCGQ01LM.html) - [AliExpress link](https://s.click.aliexpress.com/e/_dUNSKG8)
  - Xiaomi Aqara human body movement and illuminance sensor [RTCGQ11LM](https://www.zigbee2mqtt.io/devices/RTCGQ11LM.html) - [AliExpress link](https://s.click.aliexpress.com/e/_dTTUIzm)
  - Xiaomi Aqara door & window contact sensor [MCCGQ11LM](https://www.zigbee2mqtt.io/devices/MCCGQ11LM.html) - [AliExpress link](https://www.aliexpress.com/item/32967550225.html)
  - Xiaomi Mi/Aqara smart home cube [MFKZQ01LM](https://www.zigbee2mqtt.io/devices/MFKZQ01LM.html) - [AliExpress link](https://s.click.aliexpress.com/e/_dYCODwy)
  - Xiaomi Aqra Viration sensor [DJT11LM](https://www.zigbee2mqtt.io/devices/DJT11LM.html)- [Aliexpress link](https://s.click.aliexpress.com/e/_dYCODwy)
  - Xiaomi Mosquitto Repellent 
  - [QuinLED-Dig-Uno](https://quinled.info/2018/09/15/quinled-dig-uno/) for controlling addressable LED strips 
  - [Shelly EM](https://shelly.cloud/products/shelly-em-smart-home-automation-device/) energy meter with 50A clamp
  - [Shely Plug S](https://shelly.cloud/products/shelly-plug-s-smart-home-automation-device/) smart Plugs
  - Shelly Gas CNG sensor
  - Google [Chromcast devices](https://store.google.com/gb/product/chromecast?hl=en-GB)
  - LG webOS TV
  - Mi TV stick
  - tado° [Smart Thermostat](https://www.tado.com/hr/)
  - tado° [Smart Radiator Thermostat](https://www.tado.com/us/products/smart-radiator-valve)
  - various PoE IP cameras 
  - Tile [Mate 2020](https://www.thetileapp.com/en-us/store/tiles/mate)
  - Google [Home Mini](https://store.google.com/gb/product/google_home_mini_first_gen?hl=en-GB)
  - Google [Home Display](https://store.google.com/gb/product/google_nest_hub?hl=en-GB)
  - Lenovo [Smart Clock](https://www.lenovo.com/us/en/smart-clock)
  - Elgato [Key Light Air](https://www.elgato.com/en/gaming/key-light-air)


### Containers and add-ons

As I'm running this on Synology, I have mix of Docker containers and hass.io add-ons. Here is a list:

Add-ons:
  - ADB Android Debug Bridge - [link](https://github.com/hassio-addons/addon-adb)
  - Assistant Relay - [link](https://github.com/Apipa169/Assistant-Relay-for-Hassio)
  - ESPHome - [link](https://esphome.io/) - migrated from Docker container
  - Mosquitto Broker - [link](https://github.com/home-assistant/hassio-addons/tree/master/mosquitto)
  - Node-RED - [link](https://github.com/hassio-addons/addon-node-red) - in process of migration, still using Docker one
  - Visual Studio Code - [link](https://github.com/hassio-addons/addon-vscode) - migrated from Docker container
  - Zigbee2MQTT -[link](https://github.com/danielwelch/hassio-zigbee2mqtt)

Containers:
  - AdGuard Home 
  - Emby
  - Facebox
  - Grafana
  - InfluxDB
  - Node-RED
  - Portainer
  - Zigbee2MQTT - REMOVED, now using Add-on
  - MQTT - REMOVED, now using Add-on

 plus some others too - not directly related to Home Assistant (Minecraft/PaperMC, Storj node,...)


### Integrations

There are too many integrations to list them all, but some of the main ones are:
  - Telegram for notifications and control
  - Zigbee2MQTT for controlling (and now also updating) my Zigbee devices
  - Google for integration with Google Assistant and various Home devices
  - Synology for Surveillence station and Synology system statistics and info
  - HACS - Home Assistant Community Store - for even more custom components and plugins
  - influxDB - storing data generated by Home Assistant
  - OctoPrint - to see what my Ender 3 Pro 3D printer is doing
etc...

Following is a list of active Integrations that are visible at Configuration->Integration page:
  - AccuWeather
  - AdGuard
  - AirVisual
  - Blitzortung (HACS)
  - Certificate Expiry
  - COVID-19
  - Elgato Key Light
  - EPSHome
  - GDACS
  - Google Cast
  - HACS
  - Internet Printing Protocol
  - Luftdaten
  - Mikrotik
  - Minecraft Server
  - Mobile App
  - MQTT
  - Network UPS Tool
  - ONVIF
  - OpenUV
  - Reolink
  - Shelly
  - SpaceX
  - SpeedTest
  - Synology DSM
  - Tado
  - Tile
  - WLED on [QuinLED Dig-Uno](https://quinled.info/2018/09/15/quinled-dig-uno/) boards


## Folder structure and files

Insipred by [Franck](https://github.com/frenck/home-assistant-config) I've broken my configuration in various files.

It looks overwhelming at first, but when you get the hang of it, this structure is much easier to maintain and find something. Also disabeling parts of the integrations is just a rename away :)

## Counters

Current count of various things in Home Assistant 

| Type                 | Count |
| -------------------- |:-----:|
| Alerts               |     2 |
| Automations          |   132 |
| Binary sensors       |   147 |
| Cameras              |    11 |
| Climates             |     4 |
| Device trackers      |    62 |
| Entities             |  1471 |
| Groups               |    17 |
| Input Boolean        |    13 |
| Input Date/Time      |    20 |
| Input Number         |    11 |
| Input Select         |     9 |
| Input Text           |     4 |
| Lights               |    34 |
| Media players        |    31 |
| Lines of code (YAML) | 15117 |
| Persons              |     6 |
| Plants               |     4 |
| Rest commands        |    12 |
| Scripts              |    16 |
| Sensors              |   840 |
| Switches             |    73 |
| Timers               |     3 |
| Weather              |     2 |


### Missing files

Due to privacy, security,... some files are not included as well as some folders.

Here is a list of them sorted:
#### Missing folders
  - www/community

#### Missing files
Most of the missing files now have sample version. This is edited version with "fake" information, so you are able to reuse code.

  - ip_bans.yaml - could contain IP addresses  - added SAMPLE
  - secrets.yaml - contains credentials and some private infos - added SAMPLE
  - known_devices.yaml - contains indentifiers  - added SAMPLE
  - customize.yaml - contains private information - added SAMPLE
  - facebox-*.yaml - contains information for face recognition - added SAMPLE
  - google_calendars.yaml - contains private information - added SAMPLE
  - telegram_gps_response_andrej.yaml - contains identifiers - added SAMPLE
  - telegram_gps_response_luka.yaml - contains identifiers
  - telegram_gps_response_mirta.yaml - contains identifiers

Also missing are certificates, json files, cookies,...
