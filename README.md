# KeywordBot
* Forked from https://github.com/berkuhlee/KeywordBot
* http://discordpy.readthedocs.io/en/latest/api.html

Improvements
* Only allow a subset of configurable roles to access the bot
* Only allow a subset of configurable roles to access admin commands
* Only monitor a few configurable channels 


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
- the config.ini file should be self-explanatory. You can set the discord user, the server, the database settings and the protected roles (those that can't be deleted through bot commands) 
 
Running the bot
---------------
- chmod +x run.sh
- ./run.sh 



TODO
-----
- Extend manageability from direct commands
- add instructions on how to run it as a daemon
