## /entities/lights folder

In this folder, light groups are defined.
This is done according to the documentation here:

https://www.home-assistant.io/integrations/light.group/

Benefit of this is that it allows you to control group of lights as a single light and it also adapts to type of the lights inside the group.

Downside of this is that when asking Google to turn off Kitchen lights, it will say that 4 lights have been turned-off - 3 lights + kitchen_lights group.