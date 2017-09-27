# KeywordBot
* Forked from https://github.com/berkuhlee/KeywordBot
* http://discordpy.readthedocs.io/en/latest/api.html

Improvements
* Only allow a subset of configurable roles to access the bot
* Only allow a subset of configurable roles to access admin commands
* Only monitor a few configurable channels 

Improvements for pokemon go specific
* Allow users to set the minimum IV of any pokemon to monitor
* Allow users to set a radius to limit the pokemon spawns
* Allow admins to manage the monitored channels and allowed roles that can make use and/or administer the bot


Setup requirements
------------------
- python 3.4
- PIP3

After setting those up execute the following commands
- pip3 install git+https://github.com/Rapptz/discord.py@async
- pip3 install requests
- pip3 install mysqlclient
- pip3 install configparser


Initial configuration
-------------
- First make a clean checkout of the repository
- import the database under `/sql/` into your local database
- Configure the bot through `config.ini`
 
Running the bot on its own
--------------------------
- chmod +x run.sh
- ./run.sh 


Setting up the script as a service
----------------------------------
In Mac OXS using Launchd
------
- create com.discordapp.notificationbot file in /Library/LaunchDaemons with contents:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
         <key>Label</key>
         <string>com.discordapp.notificationbot</string>
         <key>ProgramArguments</key>
         <array>
              <string>/Users/maarten/Documents/git/keywordbot/daemon.sh</string>
         </array>
         <key>RunAtLoad</key>
         <true/>
         <key>KeepAlive</key>
         <true/>
         <key>Crashed</key>
         <true/>
    </dict>
</plist>
```
- tailor daemon.sh to reflect the correct path to your python3 installation
- make sure daemon.sh has execute permissions: chmod +x daemon.sh
- load up the script running the command launchctl load com.discordapp.notificationbot

In linux using upstart
------
!!!INCOMPLETE, WILL COMPLETE SOON
- sudo nano /etc/init/DiscordNotificationBotDaemon.conf
- add the following:
```bash
description "Discord - Notification bot"
author "moonstorm"
start on runlevel [2345]    

pre-start script
  echo "[`date`] Discord Notification Bot Daemon Starting" >> /var/log/discordnotificationbot.log
end script

exec /bin/sh run.sh > /dev/null & 
```


TODO
-----
- add instructions on how to run it as a daemon under linux