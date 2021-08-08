## /automations folder
 
This folder contains all of the automations I use.
Some of the automations also use scripts inside of them to run mostly TTS related tasks.
As with everything, some things could still be optimized, but that's work in progress.
 
Each automation YAML file also contains a description, but here is a brief overview.
 
### /automation/alarms
Wake-up alarms for kids during the school year. Still not finished.
Nme could be notifications, but due to how it started it's still called alarms
 
### /automation/lights
Automations related to lights.

### /automation/plants
Used to track when plant sensors have been charged last time

### /automation/switches
Xiaomi CUBE and switches automations.
 
### /automation/system
System related stuff, such as github, update notifications etc
 
### /automation/tags
NFC tag automations. Far from finished, more of proof of concept.

### /automation/telegram
Bunch of automations that can be used to control telegram bot with /commands or menus.
 
### /automation/utilities
Heating, electricity and similar automations

### /automation/weather
Weather and air quality related automations.
 
### batteries-warning.yaml:
When batteries are low, receive notification. Currently not working due to some previous breaking change.
I did use it for some time, but didn't find it useful enough.
 
### camera-balcony-motion-webhook.yaml and camera-elevator-motion-webhook.yaml:
Both of those automations are triggered on motion (by Synology Surveillance Station webhook) and are used for image recognition.
Currently, only Balcony one is active as it processes images from the camera watching the only entrance.
 
### camera-motion-stream-tv.yaml:
Test automation, used to stream camera feed to media devices. 
In the future I hope to use this automation to trigger camera feed on Google Home devices and/or TV if there is a ring on the doorbell.
 
### facebox-face-recognition-andrej_sample.yaml and other with same name:
These are used to trigger a message if the face is recognized from the ML pattern.
 
### front-door-alarm-none-home.yaml:
Very simple alarm that sends notification to all family members and also to all Google speakers, if the door is opened and no one is at home.
 
### front-door-sensor.yaml:
Not used much except to annoy everyone. Simple door open warning after 5 minutes.
 
### sunrise_notification.yaml:
Notification of sunrise with TTS script. Need to disable it in the future since it don't care if it is 5AM or weekend :)
 
### tv-time-nickelodeon.yaml:
Triggered when Nickelodeon was on for longer than 15 minutes. Pushes TTS to Google Home speaker but also shows message on LG TV

