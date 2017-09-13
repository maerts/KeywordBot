# KeywordBot
* Forked from https://github.com/berkuhlee/KeywordBot

Improvements
* Only allow a subset of configurable roles to access the bot
* Only allow a subset of configurable roles to access admin commands
* Only monitor a few configurable channels 


Setup requirements
------------------
- python 3.4
- PIP3

After setting those up execute the following commands
pip3 install git+https://github.com/Rapptz/discord.py@async
pip3 install requests


Initial configuration
-------------
options.txt    - add the user mail, password and the server ID where you want the bot to be active
admin.txt      - the roles that can execute admin commands
users.txt      - the roles that can use the bot normally
channels.txt   - the channels the bot monitors
 
