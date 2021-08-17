# league_of_legends_sensor
a custom component for displaying current League of legends ingame status in Home Assistant

![example.png](/images/preview.png)

# How to use

You will need an Riot Api key for League of Legends to use this Sensor. You can Apply for one at https://developer.riotgames.com/
Hit register Product and Apply for a `personal API Key`
once your Application is accepted you should get your API Key.

Install this Repo as a Custom Repository in Hacs or copy the folder `custom_components` from this repo into your `~/.homeassistant/` folder and restart home-assistant.

# Configuration Example
To enable the Sensor add the following Lines to your configuration.yaml file:
```
sensor:
   - platform: league_of_legends
     api_key: RGAPI-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
     players:
     - region: EUW
       name: Joshi425
```

Currently the Sensor states if the Player is currently in a Match, The Riot Api has no Way of getting the online Status.
The Following Attributes are exposed for each Player:
```
Summoner Level
Solo Queue Rank(if ranked)
Flex Queue Rank(if ranked)
```
if the Player is currently in a Match also the following Information is exposed:
```
Gamemode (aram, normals, Solo Queue, etc...)
Champion
Teammates
Side
```
Also the Icon for the Summoner is set to his current Profile Picture in League, but Updates to the Champion Picture if the Play is ingame. 

