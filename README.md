# Changelog
01/12/2017
----
* Added CP & Level tracking to the bot. Update the config.ini file to add bot.cpenable & bot.lvlenable to the [bot] section
30/11/2017
----
* Execute update-0.97-to-0.98.sql if you have an existing installation, otherwise start from dump.sql
* Added admin.super setting in config.ini (check the example) to allow the definition of superadmins outside of the in-discord settings
* Based the coordinates regex on the embed url rather than the description so the filter functionality works for defauft embed configuration.
* Added a clean database structure for the bot for new installations
28/11/2017
----
* Added configurable channel to listen for `!notification` call. Settings in config.ini under bot.triggerchannels, look at example file
* moved regex to the configuration to make them configurable for different setups
* Capture groups for the title: pokemon, level <- not mandatory, but preferably present.
* Capture groups for the description: cp, form, level, gender, region, iv, gymmoves, moves, gym <- not mandatory, but preferably present.
* Extracted the IV, CP, LEVEL from the description for future notifications on them



----
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
=====
- python 3.4
- PIP3

After setting those up execute the following commands
- pip3 install git+https://github.com/Rapptz/discord.py@async
- pip3 install requests
- pip3 install configparser
- pip3 install default-libmysqlclient-dev
- pip3 install mysqlclient


Initial configuration
=====
- First make a clean checkout of the repository
- import the database under `/sql/` into your local database
- Configure the bot through `config.ini`
 
Running the bot on its own
=====
- chmod +x run.sh
- ./run.sh 


Setting up the script as a service
=====
In Mac OXS using Launchd
-----
- create a symbolic link to the file `sudo ln -s <absolute-path-to-bot>/daemon/launchd/com.discordapp.notificationbot /Library/LaunchDaemons/com.discordapp.notificationbot`
- you have to slightly change the file to correspond to your system
- make sure daemon.sh has execute permissions: `chmod +x daemon.sh`
- load up the script running the command: `launchctl load com.discordapp.notificationbot`
- to stop the script from running, execute the command: `launchctl unload com.discordapp.notificationbot`


In Linux using systemd
-----
- create a symbolic link to the file `sudo ln -s <absolute-path-to-bot>/daemon/systemd/notificationbot.service /etc/systemd/system/notificationbot.service`
- make sure daemon.sh has execute permissions: `chmod +x daemon.sh`
- you can now control the service using systemd


Update
=====
2017-10-06 - If you update from 0.95 to 0.96, import update-0.95-to-0.96.sql into your database. Otherwise use dump.sql as a base.
