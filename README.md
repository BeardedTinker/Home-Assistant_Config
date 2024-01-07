  <h4>
    <a href="https://github.com/BeardedTinker/Home-Assistant_Config/actions"><img src="https://img.shields.io/github/workflow/status/BeardedTinker/Home-Assistant_Config/Home%20Assistant%20CI?label=GitHub%20CI&style=plastic"/></a>
    <a href="https://github.com/BeardedTinker/Home-Assistant_Config/stargazers"><img src="https://img.shields.io/github/stars/BeardedTinker/Home-Assistant_Config.svg?style=plasticr"/></a>
    <a href="https://github.com/BeardedTinker/Home-Assistant_Config/commits/master"><img src="https://img.shields.io/github/last-commit/BeardedTinker/Home-Assistant_Config.svg?style=plasticr"/></a>
    <a href="https://github.com/BeardedTinker/Home-Assistant_Config/commits/master"><img src="https://img.shields.io/github/commit-activity/y/BeardedTinker/Home-Assistant_config?style=plastic"/></a>
    <a href="https://discord.gg/HkxDRN6"><img src="https://img.shields.io/discord/675020779955683328?label=Discord%20BeardedHome&logo=discord"/></a><br>
    <a href="https://www.youtube.com/beardedtinker"><img src="https://img.shields.io/youtube/channel/subscribers/UCuqokNoK8ZFNQdXxvlE129g?style=plastic"/></a>
    <a href="https://twitter.com/BeardedTinker"><img src="https://img.shields.io/twitter/follow/BeardedTinker?style=plastic"/></a><br>


Each commit is automaticlly verified with <a href="https://github.com/BeardedTinker/Home-Assistant_Config/actions">GitHub CI</a> - where it's tested against Current installed version, Latest, Dev and Beta release. RemarkLint and YAML is also checked.
  </h4>

Contents
========

 * [Intro](#why)
 * [YouTube Channel](#youtube-channel)
 * [Hardware](#hardware)
 * [AddOns](#addons)
 * [Integrations](#integrations)
 * [Configuration](#configuration)
 * [Folder and files](#folder-and-files)
 * [Coutners](#counters)
 * [Missing files?](#missing-files)


### Intro

Here you can find all of the configuration files from my Home Assistant installation - main system or if you prefer to call it production enviroment. Updates are pushed whenever there is a change and I do try to work on the system as much as time allows. But lately it's been slow<br>
I wish to thank all of the Home Assistant community for being inspiration for lot of the things I did here.<br>
I tried to list original authors of the code or parts of the code I used, but if something is missing, I appologise.


## YouTube Channel?

A lot of integrations and automations have videos on my [YouTube channel](https://YouTube.com/BeardedTinker) - neraly 400 videos, with at least 250 of them being Home Assistant How To's. 

If you want to get in touch, you can always find me on Discord Server - [BeardedHome](https://discord.gg/HkxDRN6). 

Also, if you have time you can try and join me while streaming and there should be at 1 or 2 streams each month!

> **Note**
> Do you want to support me, you can do so by becoming my YouTube Channel member - just click [link here](https://www.youtube.com/channel/UCuqokNoK8ZFNQdXxvlE129g/join) and select one of the membership levels - or go to my merchandise store and get something there!


### Hardware

Heart of my smart home is Home Assistant OS running in Virtual Machine on [Synology DSM920+](https://www.synology.com/en-us/products/DS920+) - DSM version 6.2.4.

Plugged in Synology is Zigbee USB CC2652RB stick from [slae.sh](https://slae.sh/projects/cc2652/) with Zigbee2mqtt firmware from Koenkk (Latest available firmware).

And yes, it does have extra RAM installed for total of 20GB RAM.

From other devices that I use, here is a list:

##### IKEA DEVICES
  + IKEA TRADFRI remote control (E1524/E1810)
  + IKEA TRADFRI ON/OFF switch (E1743)
  + IKEA TRADFRI control outlet (E1603/E1702)
  + IKEA TRADFRI various bulbs of all sizes and shapes (LED1545G12, LED1623G12, LED1650R5, LED1536G5, LED1649C5, LED1736G9)
  + IKEA TRADFRI shortcut (E1812)

##### XIAOMI DEVICES
  + Xiaomi MiJia wireless switch [WXKG01LM](https://www.zigbee2mqtt.io/devices/WXKG01LM.html) - [AliExpress link](https://s.click.aliexpress.com/e/_dW7ZKDA)
  + Xiaomi MiJia temperature & humidity sensors [WSDCGQ01LM](https://www.zigbee2mqtt.io/devices/WSDCGQ01LM.html) - [AliExpress link](https://s.click.aliexpress.com/e/_dUNSKG8)
  + Xiaomi Aqara human body movement and illuminance sensors [RTCGQ11LM](https://www.zigbee2mqtt.io/devices/RTCGQ11LM.html) - [AliExpress link](https://s.click.aliexpress.com/e/_dTTUIzm)
  + Xiaomi Aqara door & window contact sensor [MCCGQ11LM](https://www.zigbee2mqtt.io/devices/MCCGQ11LM.html) - [AliExpress link](https://www.aliexpress.com/item/32967550225.html)
  + NEW Aqara Door and Window contact sensor
  + Xiaomi Mi/Aqara smart home cube [MFKZQ01LM](https://www.zigbee2mqtt.io/devices/MFKZQ01LM.html) - [AliExpress link](https://s.click.aliexpress.com/e/_dYCODwy)
  + Xiaomi Aqara Vibration sensor [DJT11LM](https://www.zigbee2mqtt.io/devices/DJT11LM.html)- [Aliexpress link](https://s.click.aliexpress.com/e/_dYCODwy)
  + Xiaomi Water sensor [SJCGQ11LM](https://www.zigbee2mqtt.io/devices/SJCGQ11LM.html) - [AliExpress link](https://www.aliexpress.com/item/4001249406915.html)
  + Xiaomi Mosquitto Repellents [ESPHome](https://youtu.be/XMFn8fKhUFA) - [AliExpress link](https://www.aliexpress.com/item/4000195100873.html)

##### SHELLY DEVICES
  + [Shelly EM](https://shelly.cloud/products/shelly-em-smart-home-automation-device/) energy meter with 50A clamp
  + [Shelly Plug S](https://shelly.cloud/products/shelly-plug-s-smart-home-automation-device/) smart Plugs
  + [Shelly Gas CNG sensor](https://shelly.cloud/products/shelly-gas-smart-home-automation-sensor/) 
  + [Shelly Motion sensor](https://shelly.cloud/shelly-motion-smart-home-automation-sensor/)
  + [Shelly Button 2.0](https://shelly.cloud/products/shelly-button-1-smart-home-automation-device/)
  + [Shelly Humidity and Temperature sensor](https://shelly.cloud/products/shelly-humidity-temperature-smart-home-automation-sensor/)
  + [Shelly 1L](https://shelly.cloud/products/shelly-1l-single-wire-smart-home-automation-relay/)
  + [Shelly Plus 2PM](https://shelly.cloud/shelly-plus-2pm/)
  + [Shelly H&T Plus](https://www.shelly.cloud/en-hr/products/product-overview/shelly-plus-h-and-t) sensor
  + [Shelly Motion 2](https://www.shelly.cloud/en-hr/products/product-overview/shelly-motion-2) sensor

  Plus some Shelly devices that are waiting installation and/or testing:
  + Shelly Uno 
  + Shelly UV light
  + Shelly Plus 1 
  + Shelly Plus 1PM 

##### SWITCHBOT DEVICES
  + [SwitchBot Contact Sensor](https://bit.ly/3ERCoYP)
  + [SwitchBot Motion Sensor](https://bit.ly/41KhXH8)
  + [SwitchBot Meter](https://bit.ly/3ETHILc)
  + [SwitchBot Meter Plus](https://bit.ly/3J6CRsC)
  + [SwitchBot Bot](https://bit.ly/3y6fs3Z)
  + [SwitchBot Remote](https://bit.ly/3Yf6XhW)
  + [SwitchBot Indoor Cam](https://bit.ly/3J81DbD)
  + [SwitchBot Pan & Tilt camera](https://bit.ly/3Zfe9fi)
  + [SwitchBot Humidifier](https://switchbot.vip/3FtfULt)
  + [SwitchBot Hub Mini](https://bit.ly/3kAoIuo)
  + [SwichBot Curtain Rod 2](https://bit.ly/3YhMWqI)
  + [SwichBot Curtain Rod 3]()
  + [SwitchBot Hub 2](https://bit.ly/3kAoIuo)
  + [SwitchBot K10+](https://bit.ly/3kAoIuo)

##### SMART SPEAKERS, DISPLAYS AND SIMILAR
  + ~~Google [Chromcast devices](https://store.google.com/gb/product/chromecast?hl=en-GB)~~
  + Google [Home Mini](https://store.google.com/gb/product/google_home_mini_first_gen?hl=en-GB)
  + Google [Home Display](https://store.google.com/gb/product/google_nest_hub?hl=en-GB)
  + Amazon [Echo 3rd Gen](https://amzn.to/3YiL7tU)
  + Lenovo [Smart Clock](https://www.lenovo.com/us/en/smart-clock)
  + LG webOS TV
  + Chromcast with [Google TV 4K](https://amzn.to/3ZDr9Ld) stick 

##### HEATING
  + tado° [Smart Thermostat + bridge](https://amzn.to/3KRZ2nJ)
  + tado° [Smart Radiator Thermostat](https://amzn.to/3mkmwaS)
  + tado° [Smart AC+ controller](https://amzn.to/3KTYyNM)
  + tado° [Smart AddOn Smart Thermsotat](https://amzn.to/3kKcO0M)
  
##### CAMERAS
  + [Reolink RLC-811A 8MP PoE camera](https://bit.ly/3xu9sBx )
  + [SwitchBot Indor Cam](https://switchbot.vip/3QOpBue)
  + [SwitchBot Pan/Tilt Cam](https://switchbot.vip/3NiAJN1)
  + various DLink PoE IP cameras 
  
##### OTHER INTEGRATED DEVICES
  ~~- Tile [Mate 2020](https://amzn.to/3KRYM8f)~~
  - Elgato [Key Light Air](https://amzn.to/3IOe8Ib)
  - [Roborock S5 max](https://amzn.to/3kBFw49)
  - [QuinLED-Dig-Uno](https://quinled.info/2018/09/15/quinled-dig-uno/) for controlling addressable LED strips
  - [ioios.io](https://ioios.io/) Pithy Display and Pithy Pixel 
  - [Nuki 2.0 Combo](https://nuki.io/en/smart-lock/) Smart Door lock with bridge 
  - [Nuki Opener](https://amzn.to/41Jnb5V/) for intercom
  - [Voron 2.4 R2](https://vorondesign.com/voron2.4) 3D printer (Klipper)
  - LilyGo TTgo HiGrow boards (with @peasor and ESPHome firmware)
  - HP DeskJest All-in-on printer
  - [Withings Thermo](https://amzn.to/3YhQJEs) Smart thermometer
  - Sonoff [NSPanel Pro]()
  - Sonoff [Thermo]()
  - Zigbee [Plant Sensor]()

### AddOns

As I'm running this on Synology, I have mix of Docker containers and Home Assistant add-ons. Here is a list:

Add-ons:
  - Advanced SSH & Web Terminal 
  - ESPHome - [link](https://esphome.io/) 
  - openWakeWorkd
  - Piper
  - Samba Backup - [link](https://github.com/thomasmauerer/hassio-addons)
  - Samba share - [link](https://github.com/home-assistant/hassio-addons/tree/master/samba)
  - Studio Code Server - [link](https://github.com/hassio-addons/addon-vscode)
  - Terminal & SSH - [link](https://github.com/home-assistant/hassio-addons/tree/master/ssh)
  - Uptime Kuma - [link](https://github.com/hassio-addons/addon-uptime-kuma)
  - Whisper
  - Zigbee2MQTT -[link](https://github.com/zigbee2mqtt/hassio-zigbee2mqtt/tree/master/zigbee2mqtt)
  - ZigStar Silicon Labs FW Flasher
  - ZigStar TI CC2652P/P7 FW Flasher


Containers:
  - VaultWarden - opens source version of BitWarden as password manager
  - Grafana - only used currently for Storj node status
  - MQTT - used by all Zigbee devices, some Shelly devices, printing and more
  - Portainer - for Docker management and monitoring
  - Prometheus - for Storj node data logging
  - Smokeping - tracking network device activity
  - Storagenode - Storj node for renting free space
  - Storj Exporter - exports statistics from node to Prometheus
  - UniFi controller - configuration and management of UniFi devices

### Integrations

There are too many integrations to list them all, but some of the main ones are:
  - Telegram for notifications and control
  - Zigbee2MQTT for controlling (and now also updating) my Zigbee devices
  - Google for integration with Google Assistant and various Home devices
  - Synology for Surveillence station and Synology system statistics & info
  - HACS - Home Assistant Community Store - for even more custom components and plugins
etc...

Following is a list of active Integrations that are visible at Configuration->Integration page:
  - AccuWeather
  - AirVisual
  - Alexa Media Player
  - Android Debug Bridge
  - Android TV Remote
  - Anniversaries
  - Apple TV 
  - Battery Note (*)
  - Blitzortung (HACS)
  - Certificate Expiry
  - Cloudflare
  - ColorExtractor
  - Discord
  - DLNA server
  - Electricity maps
  - Elgato Key Light
  - ESPHome
  - FAst.com (*)
  - Forcast Solar
  - Generic camera
  - GitHub
  - GDACS
  - Google Assistant 
  - Google Assistant SDK
  - Google Calendar
  - Google Cast
  - Google Sheets
  - HACS
  - HASS Agent
  - Home Assistant Supervisor
  - HomeKit Devices
  - iBeacon Tracker
  - International Space Station
  - Internet Printing Protocol
  - Jellyfin 
  - Launch library
  - LG webOS Smart TV
  - Met.No
  - Mikrotik
  - Minecraft Server
  - MJPEG IP Camera
  - Mobile App
  - Moon
  - MQTT
  - Network UPS Tool
  - Nuki lock
  - ONVIF
  - OpenUV
  - OurGroceries (*)
  - Ping (*)
  - PowerCalc
  - Radio Browser
  - Reolink IP/NVR Camera
  - Season
  - Sensor Community
  - Shelly
  - Shopping List
  - Sonos
  - SpeedTest
  - Sun
  - SwitchBot
  - Synology DSM
  - Tado
  - Thread
  - Tile
  - Tuya Local 
  - Twitch
  - UniFi Network
  - Uptime 
  - Uptime Kuma
  - Version
  - Voice over IP
  - Watchman
  - Withings
  - WLED on [QuinLED Dig-Uno](https://quinled.info/2018/09/15/quinled-dig-uno/) boards
  - Workday
  - Wyoming Protocol 
  - Xiaomi BLE
  - Xiaomi Miio
  - yTubeMusic

(*) marks new since last update

## Folder and files

Insipred by [Franck](https://github.com/frenck/home-assistant-config) I've broken my configuration in various files.

It looks overwhelming at first, but when you get the hang of it, this structure is much easier to maintain and find something. Also disabeling parts of the integrations is just a rename away :)

## Counters

Up-to-date count of various things in Home Assistant 

| Type                 | Count |
| -------------------- |:-----:|
| Alerts               |     4 |
| Automations          |   193 |
| Binary sensors       |   321 |
| Cameras              |    15 |
| Climates             |    17 |
| Counters             |     4 |
| Device trackers      |   163 |
| Entities             |  4017 |
| Groups               |    17 |
| Image Processing     |     0 |
| Input Boolean        |    19 |
| Input Date/Time      |    29 |
| Input Number         |     8 |
| Input Select         |     8 |
| Input Text           |     7 |
| Lights               |    49 |
| Lines of code (YAML) |102141 |
| Locks                |     7 |
| Media players        |    31 |
| Persons              |     6 |
| Plants               |     9 |
| Rest commands        |    13 |
| Scripts              |    23 |
| Sensors              |  2394 |
| Switches             |   190 |
| Timers               |     4 |
| Utility Meters       |     5 |
| Vacuums              |     1 |
| Weather              |     3 |
* Updated: 07.01.2024 11:00 AM

### Missing files

Due to privacy, security,... some files are not included as well as some folders.

Here is a list of them sorted:
#### Missing folders
  - www/community

#### Missing files

> **Warning**
> Even if you don't make your configuration private - please use secrets.yaml file to store all your application credentials if needed for Home Assistant.

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
