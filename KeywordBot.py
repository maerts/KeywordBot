import asyncio  
import discord
import re
import datetime
import os
import configparser
import traceback
import MySQLdb
import logging
import requests
import math
import gc
import json
from datetime import date
from time import sleep

## Get configuration from ini file
## No validation on its presence, so make sure these are present
config = configparser.RawConfigParser()
config.read('config.ini')
# - discord config
discord_user = config.get('discord', 'discord.user')
discord_pass = config.get('discord', 'discord.pass')
discord_server = config.get('discord', 'discord.serverid')
# - db config
sql_user = config.get('sql', 'sql.user')
sql_pass = config.get('sql', 'sql.pass')
sql_host = config.get('sql', 'sql.host')
sql_port = int(config.get('sql', 'sql.port'))
sql_db = config.get('sql', 'sql.db')
# - protected roles
protected_roles = config.get('protected', 'protected.roles')
# - parse bot info
bot_spawn = config.get('bot', 'bot.spawn')
bot_raid = config.get('bot', 'bot.raid').split(',')
bot_keywordlimit = int(config.get('bot', 'bot.keywordlimit'))
bot_triggerchannels = config.get('bot', 'bot.triggerchannels').split(',')
bot_ivenable = int(config.get('bot', 'bot.ivenable'))
bot_cpenable = int(config.get('bot', 'bot.cpenable'))
bot_lvlenable = int(config.get('bot', 'bot.lvlenable'))
bot_debug = int(config.get('bot', 'bot.debug'))
bot_version = config.get('bot', 'bot.version')
bot_gapi = config.get('bot', 'bot.gapi')
# - admin build superadminlist
super_admin = config.get('admin', 'admin.super').split(',')
# - regex from config
regex_title=config.get('regex', 'regex.title')
regex_desc=config.get('regex', 'regex.desc')


# Create dictionaries placeholders, on_ready they will be filled up from db.
notifications_list = {}
notifraid_list = {}
roles_list = {}
channel_list = []
iv_list = {}
cp_list = {}
lvl_list = {}
coord_list = {}
spawn_cache_list = []

# Start discord client
client = discord.Client()

@client.async_event
def on_ready():
    global notifications_list
    global notifraid_list
    global channel_list
    global roles_list
    global iv_list
    global cp_list
    global lvl_list
    global coord_list
    notifications_list = updatedictionary()
    notifraid_list = updateraiddictionary()
    channel_list = chanmon()    
    roles_list = rolesdictionary()
    iv_list = updateivdictionary()
    cp_list = updatecpdictionary()
    lvl_list = updatelvldictionary()
    coord_list = coorddictionary()
    watchdog('Connected! Ready to notify.')
    watchdog('Username: ' + client.user.name)
    watchdog('ID: ' + client.user.id)
    watchdog('Version: ' + bot_version)
    watchdog('--Server List--')
    server = client.get_server(discord_server)    
    watchdog(server.id + ': ' + server.name)
    watchdog('-- Channels --'.ljust(50) + 'monitored')
    for channel in server.channels:
        c_mon = '[*]' if channel.id in channel_list else '[ ]'
        watchdog((channel.id + ': ' + channel.name).ljust(50) + c_mon)
    watchdog('Regexes from config')
    watchdog(regex_title)
    watchdog(regex_desc)
    

# --- Help messages ---
# The !help message for normal users
helpmsg = "Hi I'm a notification bot!\n\
\n\
`!notify {keyword} {raid} {spawn}` to add/update a PM notification about a certain pokemon raid and/or spawn. The value for raid/spawn is either 1 to track or 0 to not track. Example: `!notify tyranitar 1 1`\n\
`!notifydel {keyword}` to delete it. Example: `!notifydel tyranitar`\n\
`!notifications` for a list of your current notifications.\n\
`!keywords help` not sure which strings to add? Send this command to the bot and you'll get an overview.\n\
"
# IV user help
if bot_ivenable == 1:
    helpmsg += "`!ivadd {number}` to add iv tracking equal or above a certain number e.g. `!ivadd 80`.\n`!ivdel` to remove IV tracking.\n`!ivinfo` to show if you have IV tracking enabled.\n"
# IV user help
if bot_cpenable == 1:
    helpmsg += "`!cpadd {number}` to add cp tracking equal or above a certain number e.g. `!cpadd 2000`.\n`!cpdel` to remove cp tracking.\n`!cpinfo` to show if you have cp tracking enabled.\n"
# IV user help
if bot_lvlenable == 1:
    helpmsg += "`!lvladd {number}` to add level tracking equal or above a certain number e.g. `!lvladd 28`.\n`!lvldel` to remove level tracking.\n`!lvlinfo` to show if you have level tracking enabled.\n"
# GEO user help
helpmsg += "`!geo {number} {address}` to limit all tracking to a certain radius in km. This allows for only nearby alerts to appear e.g. `!geo 1 300 Dufferin Ave, London, ON`.\n`!geodel` to remove the radius restrictions from tracking.\n`!geonfo` to shows the currently set radius limitations you have setup.\n"
 

# The !help message for admin users
helpamsg = "\n\n\
Admin commands\n\
\n\
`!chanlst` print all channels and which ones are monitored by me.\n\
`!chanadd {id}` add the channel with the id to the monitored list.\n\
`!chandel {id}` remove the channel from the monitored list.\n\
`!rolelst` print all roles that can use notification commands (non admin).\n\
`!roleadd {id} {user} {admin}` give arole access to the notification bot, {id} is the roleid as shown in !rolelst, {user} & {admin} are 1 or 0.\n\
`!roledel {id}` delete a role from the database of the notification bot.\n\
`!keywordcleanup` this force cleans the notification database (old users and their notifications will be purged)\n\
`!botstats` this returns userdata in the bot.\n\
"
# IV admin help
if bot_ivenable == 1:
    helpamsg += "`!ivlist` this returns iv tracking list in the bot.\n"

# The message shown for unprivileged users
noaccessmsg = "Hi I'm a notification bot!\n\
\n\
Unfortunately you do not have the proper permissions to use me, read #announcements for more information on how to donate to get access. If you believe this is in error, try again in a few minutes. Sometimes due to slow response times from Discord I can't find your permissions."
# --- End help messages ---

@client.async_event
def on_message(message):
    global notifications_list
    global notifraid_list
    global channel_list
    iv_enabled = bot_ivenable == 1
    cp_enabled = bot_cpenable == 1
    lvl_enabled = bot_lvlenable == 1
    access_admin = roleacc(message, 'admin')
    access_user = roleacc(message, 'user')
    if message.channel.id in bot_triggerchannels and not message.channel.is_private and '!notification' == message.content[0:13]:
        if access_user or access_admin:
            server = client.get_server(discord_server)
            usr = server.get_member(message.author.id)
            yield from client.send_message(usr, "Hi, I'm a notificationbot, to see which commands are available to you, send a message `!help` to me.")
        return
    if message.channel.id not in channel_list and not message.channel.is_private:
        return
    if message.author == client.user:
        return
    if message.channel.is_private:
        if not access_user and not access_admin:
            yield from client.send_message(message.channel, noaccessmsg)
        elif '!help' == message.content[0:5]:
            yield from client.send_message(message.channel, helpmsg)
            if access_admin:
                yield from client.send_message(message.channel, helpamsg)
            

    # Handle incoming messages and filter them for keywords.
    try:
        yield from custom_notifications(message)
            
    except:
        try:
            ret = message.content
            if len(message.embeds) == 1:
                ret = message.embeds[0]['title']
            watchdog('Nobody has trigger for: '+ ret)
        except:
            watchdog('probably some special character in message.content')            
    yield from if_add(message)
    yield from if_delete(message)

    
    if '!update' == message.content[0:7] and access_admin:
        notifications_list = updatedictionary()
        notifraid_list = updateraiddictionary()
    elif '!chanlst' == message.content[0:8] and access_admin:
        yield from chanlst(message)
    elif '!chanadd' == message.content[0:8] and access_admin:
        yield from chanadd(message)
    elif '!chandel' == message.content[0:8] and access_admin:
        yield from chandel(message)
    elif '!ivinfo' == message.content[0:7] and iv_enabled and access_user:
        yield from ivinfo(message)
    elif '!ivadd' == message.content[0:6] and iv_enabled and access_user:
        yield from ivadd(message)
    elif '!ivdel' == message.content[0:6] and iv_enabled and access_user:
        yield from ivdel(message)
    elif '!ivlist' == message.content[0:7] and iv_enabled and access_admin:
        yield from ivlist(message)
    elif '!cpinfo' == message.content[0:7] and cp_enabled and access_user:
        yield from cpinfo(message)
    elif '!cpadd' == message.content[0:6] and cp_enabled and access_user:
        yield from cpadd(message)
    elif '!cpdel' == message.content[0:6] and cp_enabled and access_user:
        yield from cpdel(message)
    elif '!cplist' == message.content[0:7] and cp_enabled and access_admin:
        yield from cplist(message)
    elif '!lvlinfo' == message.content[0:8] and lvl_enabled and access_user:
        yield from lvlinfo(message)
    elif '!lvladd' == message.content[0:7] and lvl_enabled and access_user:
        yield from lvladd(message)
    elif '!lvldel' == message.content[0:7] and lvl_enabled and access_user:
        yield from lvldel(message)
    elif '!lvllist' == message.content[0:8] and lvl_enabled and access_admin:
        yield from lvllist(message)
    elif '!roleadd' == message.content[0:8] and access_admin:
        yield from roleadd(message)
    elif '!roledel' == message.content[0:8] and access_admin:
        yield from roledel(message)
    elif '!rolelst' == message.content[0:8] and access_admin:
        yield from rolelst(message)
    elif '!keywordcleanup' == message.content[0:15] and access_admin:
        yield from keywords_cleanup(message)
    elif '!botstats' == message.content[0:9] and access_admin:
        yield from botstats(message)
    elif '!notifications' == message.content[0:14] and access_user:
        yield from mynotifications(message)
    elif '!geo ' == message.content[0:5] and access_user:
        yield from geolocation(message)
    elif '!geodel' == message.content[0:7] and access_user:
        yield from geodel(message)
    elif '!geonfo' == message.content[0:7] and access_user:
        yield from geonfo(message)
    elif '!keywords help' == message.content[0:14] and access_user:
        yield from keywords_help(message)

##################################################

# --- Helper function ---
def keywords_help(message):
    cwd = os.getcwd()
    watchdog(cwd)
    yield from client.send_message(message.author, "If you have any problems setting up keywords, I look for the following triggers.")
    yield from client.send_message(message.author, "For raid eggs we cap the following strings.")
    with open(cwd + '/raidegg.png', 'rb') as f:
        result = yield from client.send_file(message.channel, f)
        watchdog(str(result))
    yield from client.send_message(message.author, "For hatched raids we cap the following strings.")
    with open(cwd + '/raidmon.png', 'rb') as f:
        result = yield from client.send_file(message.channel, f)
        watchdog(str(result))
    yield from client.send_message(message.author, "For wild pokemons we cap the following strings.")
    with open(cwd + '/spawn.png', 'rb') as f:
        result = yield from client.send_file(message.channel, f)
        watchdog(str(result))

# -- End Helper function ---

# --- notification functions ---
# General catch all for all speech to pick up on keywords.
def custom_notifications(message):
    global roles_list
    global notifications_list
    global notifraid_list
    server = client.get_server(discord_server)
    if message.channel.name == None:
        return
    msglist = message.content.lower().split()
    embed = False
    
    # Initialize coordinate placeholders
    coords = False
    lng = 0.0
    lat = 0.0
    reg_iv = 0.0
    reg_cp = 0
    reg_level = 0
    pokemonname = ""
    if len(message.embeds) == 1:
        embed = True
        keywordlist = []
        # Regex the title for more concise keywords.
        watchdog(message.embeds[0]['title'].lower())
        regex = _regex_from_encoded_pattern(regex_title)
        match_title = regex.match(message.embeds[0]['title'].lower())
        try:
            # Add pokemon name if found
            if match_title.group('pokemon') is not None and match_title.group('pokemon') != "":
                keywordlist.append(match_title.group('pokemon'))
                pokemonname = match_title.group('pokemon')
        except:
            watchdog('Error getting title capture group pokemon.')

        try:
            if match_title.group('level') is not None and match_title.group('level') != "":
                keywordlist.append(match_title.group('level').strip())
        except:
            watchdog('Error getting title capture group level.')

        # Regex the description for more concise keywords.
        regex = _regex_from_encoded_pattern(regex_desc)
        match_desc = regex.match(message.embeds[0]['description'].lower())
        # put the revelant matches to a variable. We don't want to cycle too many values. This slows the script down.
        try:
            # Add the unown form
            if match_desc.group('form') is not None and match_desc.group('form') != "":
                keywordlist.append(match_desc.group('form'))
        except:
            watchdog('Error parsing the form capture group from the description.')
        
        try:
            # Add the region
            if match_desc.group('region') is not None and match_desc.group('region') != "":
                keywordlist.append(match_desc.group('region'))
        except:
            watchdog('Error parsing the region capture group from the description.')
            
        try:
            # Add the gym
            if match_desc.group('gym') is not None and match_desc.group('gym') != "":
                keywordlist.append(match_desc.group('gym'))
        except:
            watchdog('Error parsing the gym capture group from the description.')
            
        try:
            # Add moves if found
            if match_desc.group('moves') is not None and match_desc.group('moves') != "":
                m_moves_split = match_desc.group('moves').split("/")
                keywordlist.append(m_moves_split[0].strip())
                keywordlist.append(m_moves_split[1].strip())
        except:
            watchdog('Error parsing the moves capture group from the description.')
            
        try:
            # Add moves from raid if found
            if match_desc.group('gymmoves') is not None and match_desc.group('gymmoves') != "":
                m_moves_split = match_desc.group('gymmoves').split("/")
                keywordlist.append(m_moves_split[0].strip())
                keywordlist.append(m_moves_split[1].strip())
        except:
            watchdog('Error parsing the gym moves capture group from the description.')
            
        try:
            # -- Store for future improvements
            # Get the IV
            if match_desc.group('iv') is not None and match_desc.group('iv') != "?":
                reg_iv = match_desc.group('iv')
        except:
            watchdog('Error parsing the iv capture group from the description.')
            
        try:
            # Get the CP
            if match_desc.group('cp') is not None and match_desc.group('cp') != "?":
                reg_cp = match_desc.group('cp')
        except:
            watchdog('Error parsing the cp capture group from the description.')
            
        try:    
            # Get the Level
            if match_desc.group('level') is not None and match_desc.group('level') != "?":
                reg_level = match_desc.group('level')
        except:
            watchdog('Error parsing the level capture group from the description.')

        key_string = " ".join(keywordlist)
        keywordlist = keywordlist + key_string.split()
        watchdog('[iv: ' + str(reg_iv) + ',cp: ' + str(reg_cp) + ',lvl: ' + str(reg_level) + ']')
        watchdog(str(keywordlist))
        
        if len(keywordlist) > 0:
            msglist = keywordlist
        else:
            title = re.sub('[^a-zA-Z0-9 \.]', ' ', message.embeds[0]['title']).lower().split()
            desc = re.sub('[^a-zA-Z0-9 \.]', ' ', message.embeds[0]['description']).lower().split()
            msglist = msglist + title + desc


        # coordinates lookup
        coord_l = []
        # Attempt to extract the coordinates
        try:
            tmp = message.content
            if embed:
                tmp = ' '.join([message.embeds[0]['url'].lower()])
            regex = _regex_from_encoded_pattern('/.*maps\.google\.com\/maps\?q\=([^\?]*).*/si')
            coord_l = regex.findall(tmp)
            watchdog(str(coord_l))
        except:
            watchdog('Something went wrong parsing')
        if len(coord_l) == 1:
            # Parse string to float to int (otherwise critical error)
            coord_split = coord_l[0].split(',')
            lat = float(coord_split[0])
            lng = float(coord_split[1])
            coords = True
    
    ######
    # Loop through raids
    if message.author.name in bot_raid:
        watchdog('looking for raids')
        for keyword in notifraid_list.keys():
            if keyword in msglist:
                for user_id in notifraid_list[keyword]: # if empty, does nothing
                    # Make sure we don't notify users whose access has been revoked
                    usr = server.get_member(user_id)
                    revoke = True
                    for role in usr.roles:
                        if role.id in roles_list.keys() and roles_list[role.id]['user'] == 1:
                            revoke = False
                            break
                    aname = message.author.name
                    if coords and geolookup(user_id, lng, lat) == False: # if outside the users defined range
                        watchdog('The raid is out of the user {} his defined range'.format(usr.display_name))
                        pass
                    elif user_id == message.author.id or revoke: # if no access and slipped through
                        watchdog('Invalid user: same user or role with access revoked')
                        pass
                    elif embed:
                        try:
                            emb_title = '\'{}\' raid has opened up'.format(keyword, message.channel.name)
                            emb_desc = str(message.embeds[0]['description'])
                            emb_url = str(message.embeds[0]['url'])
                            emb = discord.Embed(title=emb_title, description=emb_desc, url=emb_url)
                            emb.set_image(url=str(message.embeds[0]['image']['url']))
                            emb.set_thumbnail(url=str(message.embeds[0]['thumbnail']['url']))
                            yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), embed=emb)
                        except discord.DiscordException as de:
                            watchdog(str(de.message))
                            yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), '`{}` raid has opened up. {}'.format(keyword, message.embeds[0]['url']))
                        watchdog('`{}` raid has opened up. {}'.format(keyword, message.embeds[0]['url']))
                    else:
                        yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), '`{} mentioned` **{}** `in #{}:` {}'.format(aname, keyword, message.channel.name, message.content))
                        watchdog('{} mentioned {} in #{}: {}'.format(aname, keyword, message.channel.name, message.content))
    elif message.author.name == bot_spawn:
        entry = str(lng) + " " + str(lat)
        if entry not in spawn_cache_list:
            if len(spawn_cache_list) >= 10:
                spawn_cache_list.pop(0)
                watchdog('Popped from list current length {}'.format(str(spawn_cache_list)))
            spawn_cache_list.append(entry)

            watchdog('looking for spawns')
            # Exclude list in case an IV notification was sent.
            exclude = []
            watchdog('looking through iv')
            if bot_ivenable == 1 and int(float(reg_iv)) is not 0:
                # Parse string to float to int (otherwise critical error)
                iv = int(float(reg_iv))
                # Cycle through the dictionary of IV monitors
                for user_id in iv_list.keys():
                    watchdog(user_id + ':' + iv_list[user_id])
                    # If the found IV is equal or higher than the one stored for this user, do things.
                    if coords and geolookup(user_id, lng, lat) == False:
                        watchdog('The spawn is out of the user {} his defined range'.format(user_id))
                        pass
                    elif int(iv_list[user_id]) <= iv:
                        usr = None
                        for member in server.members:
                            if member.id == user_id:
                                usr = member
                                break
                        if usr != None:
                            revoke = True
                            for role in usr.roles:
                                if role.id in roles_list.keys() and roles_list[role.id]['user'] == 1:
                                    revoke = False
                                    break
                            if user_id == message.author.id or revoke:
                                watchdog('Invalid user: same user or role with access revoked')
                                pass
                            elif embed:
                                watchdog('in embed')
                                # Store it so the user isn't notified twice.
                                exclude.append(user_id)
                                try:
                                    emb_title = 'IV ({}) equal or higher than [{}] was detected for a [{}]'.format(iv, iv_list[user_id], message.embeds[0]['title'])
                                    emb_desc = str(message.embeds[0]['description'])
                                    emb_url = str(message.embeds[0]['url'])
                                    emb = discord.Embed(title=emb_title, description=emb_desc, url=emb_url)
                                    emb.set_image(url=str(message.embeds[0]['image']['url']))
                                    emb.set_thumbnail(url=str(message.embeds[0]['thumbnail']['url']))
                                    watchdog('trying embed')
                                    yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), embed=emb)
                                except discord.DiscordException as de:
                                    watchdog(str(de.message))
                                    yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), 'IV ({}) equal or higher than `[{}] was detected` `in #{}`'.format(iv, iv_list[user_id], message.channel.name))
                                watchdog('IV ({}) equal or higher than `[{}] was detected` `in #{}`'.format(iv, iv_list[user_id], message.channel.name))
                            else:
                                yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), 'IV ({}) equal or higher than `[{}] was detected` `in #{}`'.format(iv, iv_list[user_id], message.channel.name))
                                watchdog('{} mentioned {} in #{}: {}'.format(message.author.name, iv_list[user_id], message.channel.name, message.content))

            watchdog('looking through cp')
            if bot_cpenable == 1 and int(str(reg_cp)) != 0:
                # Parse string to float to int (otherwise critical error)
                cp = int(float(reg_cp))
                # Cycle through the dictionary of cp monitors
                for user_id in cp_list.keys():
                    watchdog(user_id + ':' + cp_list[user_id])
                    # If the found cp is equal or higher than the one stored for this user, do things.
                    if coords and geolookup(user_id, lng, lat) == False:
                        watchdog('The spawn is out of the user {} his defined range'.format(user_id))
                        pass
                    if str(user_id) in exclude: # excluded from IV match
                        watchdog('User already notified with IV')
                        pass
                    elif int(cp_list[user_id]) <= cp:
                        usr = None
                        for member in server.members:
                            if member.id == user_id:
                                usr = member
                                break
                        if usr != None:
                            revoke = True
                            for role in usr.roles:
                                if role.id in roles_list.keys() and roles_list[role.id]['user'] == 1:
                                    revoke = False
                                    break
                            if user_id == message.author.id or revoke:
                                watchdog('Invalid user: same user or role with access revoked')
                                pass
                            elif embed:
                                watchdog('in embed')
                                # Store it so the user isn't notified twice.
                                exclude.append(user_id)
                                try:
                                    emb_title = 'cp ({}) equal or higher than [{}] was detected for a [{}]'.format(cp, cp_list[user_id], message.embeds[0]['title'])
                                    emb_desc = str(message.embeds[0]['description'])
                                    emb_url = str(message.embeds[0]['url'])
                                    emb = discord.Embed(title=emb_title, description=emb_desc, url=emb_url)
                                    emb.set_image(url=str(message.embeds[0]['image']['url']))
                                    emb.set_thumbnail(url=str(message.embeds[0]['thumbnail']['url']))
                                    watchdog('trying embed')
                                    yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), embed=emb)
                                except discord.DiscordException as de:
                                    watchdog(str(de.message))
                                    yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), 'cp ({}) equal or higher than `[{}] was detected` `in #{}`'.format(cp, cp_list[user_id], message.channel.name))
                                watchdog('cp ({}) equal or higher than `[{}] was detected` `in #{}`'.format(cp, cp_list[user_id], message.channel.name))
                            else:
                                yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), 'cp ({}) equal or higher than `[{}] was detected` `in #{}`'.format(cp, cp_list[user_id], message.channel.name))
                                watchdog('{} mentioned {} in #{}: {}'.format(message.author.name, cp_list[user_id], message.channel.name, message.content))
            
            watchdog('looking through level')
            if bot_lvlenable == 1 and int(str(reg_level)) != 0:
                # Parse string to float to int (otherwise critical error)
                lvl = int(float(reg_level))
                # Cycle through the dictionary of lvl monitors
                for user_id in lvl_list.keys():
                    watchdog(user_id + ':' + lvl_list[user_id])
                    # If the found lvl is equal or higher than the one stored for this user, do things.
                    if coords and geolookup(user_id, lng, lat) == False:
                        watchdog('The spawn is out of the user {} his defined range'.format(user_id))
                        pass
                    if str(user_id) in exclude: # excluded from IV match
                        watchdog('User already notified with IV')
                        pass
                    elif int(lvl_list[user_id]) <= lvl:
                        usr = None
                        for member in server.members:
                            if member.id == user_id:
                                usr = member
                                break
                        if usr != None:
                            revoke = True
                            for role in usr.roles:
                                if role.id in roles_list.keys() and roles_list[role.id]['user'] == 1:
                                    revoke = False
                                    break
                            if user_id == message.author.id or revoke:
                                watchdog('Invalid user: same user or role with access revoked')
                                pass
                            elif embed:
                                watchdog('in embed')
                                # Store it so the user isn't notified twice.
                                exclude.append(user_id)
                                try:
                                    emb_title = 'lvl ({}) equal or higher than [{}] was detected for a [{}]'.format(lvl, lvl_list[user_id], message.embeds[0]['title'])
                                    emb_desc = str(message.embeds[0]['description'])
                                    emb_url = str(message.embeds[0]['url'])
                                    emb = discord.Embed(title=emb_title, description=emb_desc, url=emb_url)
                                    emb.set_image(url=str(message.embeds[0]['image']['url']))
                                    emb.set_thumbnail(url=str(message.embeds[0]['thumbnail']['url']))
                                    watchdog('trying embed')
                                    yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), embed=emb)
                                except discord.DiscordException as de:
                                    watchdog(str(de.message))
                                    yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), 'lvl ({}) equal or higher than `[{}] was detected` `in #{}`'.format(lvl, lvl_list[user_id], message.channel.name))
                                watchdog('lvl ({}) equal or higher than `[{}] was detected` `in #{}`'.format(lvl, lvl_list[user_id], message.channel.name))
                            else:
                                yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), 'lvl ({}) equal or higher than `[{}] was detected` `in #{}`'.format(lvl, lvl_list[user_id], message.channel.name))
                                watchdog('{} mentioned {} in #{}: {}'.format(message.author.name, lvl_list[user_id], message.channel.name, message.content))

            for keyword in notifications_list.keys():
                if keyword in msglist:
                    watchdog('keyword in list :' + keyword)
                    for user_id in notifications_list[keyword]: # if empty, does nothing
                        # Make sure we don't notify users whose access has been revoked
                        usr = server.get_member(user_id)
                        watchdog("user `{}`: `{}`".format(usr.id, keyword))
                        revoke = True
                        for role in usr.roles:
                            if role.id in roles_list.keys() and roles_list[role.id]['user'] == 1:
                                revoke = False
                                break
                        if str(user_id) in exclude: # excluded from IV match
                            watchdog('User already notified with IV')
                            pass
                        elif coords and geolookup(user_id, lng, lat) == False: # limited in radius
                            watchdog('The spawn is out of the user {} his defined range'.format(usr.name))
                            pass
                        elif user_id == message.author.id or revoke: # no access and slipped through
                            watchdog('Invalid user: same user or role with access revoked')
                            pass
                        elif embed:
                            watchdog('in embed')
                            try:
                                emb_title = '`{}` spawn found, triggered by keyword `{}`'.format(message.embeds[0]['title'], keyword)
                                emb_desc = str(message.embeds[0]['description'])
                                emb_url = str(message.embeds[0]['url'])
                                emb = discord.Embed(title=emb_title, description=emb_desc, url=emb_url)
                                emb.set_image(url=str(message.embeds[0]['image']['url']))
                                emb.set_thumbnail(url=str(message.embeds[0]['thumbnail']['url']))
                                yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), embed=emb)
                            except discord.DiscordException as de:
                                watchdog(str(de.message))
                                yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), '`{} mentioned` **{}** `in #{}:` {}'.format('Bot', keyword, message.channel.name, str(message.embeds[0]['title'] + " - " + message.embeds[0]['url'])))
                            watchdog('{} mentioned {} in #{}: {}'.format(message.author.name, keyword, message.channel.name, str(message.embeds[0]['title'] + " - " + message.embeds[0]['url'])))
                        else:
                            yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), '`{} mentioned` **{}** `in #{}:` {}'.format(message.author.name, keyword, message.channel.name, message.content))
                            watchdog('{} mentioned {} in #{}: {}'.format(message.author.name, keyword, message.channel.name, message.content))

# !notify {keyword}
def if_add(message):
    global notifications_list
    global notifraid_list
    # message.author.id to add to files list
    if '!notify ' == message.content[0:8]:
        if not roleacc(message, 'user'):
            return
        msg = message.content.lower().split()
        if len(msg) < 4:
            yield from client.send_message(message.channel, "You are missing a parameter for the command, please verify and retry.")
        else:
            # Build keyword with spaces
            keyword = ""
            for x in range(1, len(msg)-2):
                keyword = keyword + " " + stripchars(msg[x]).strip()
            keyword = keyword.strip()
            # Run the keyword through levenshtein
            levenshtein = pokemon_autocorrect(keyword)
            # get the raid & spawn tracking value
            raid = stripchars(msg[len(msg)-2])
            spawn = stripchars(msg[len(msg)-1])
            watchdog('Keyword: ' + keyword)
            watchdog('Raid: ' + raid)
            watchdog('Spawn: ' + spawn)

            if levenshtein != keyword and levenshtein != "":
                yield from client.send_message(message.channel, "Did you mean any of the following: `{}`? Correct if you made a mistake with one of the suggestions.".format(levenshtein, keyword, raid, spawn))
            else:
                db = db_connect()
                c = db.cursor()
                c.execute("SELECT count(1) FROM notificationbot_keywords WHERE discord_id = '{}';".format(message.author.id))
                d = c.fetchone()
                c.close()
                db_close(db)
                watchdog('Checking existing lists for entries')
                in_spawn = keyword in notifications_list.keys() and message.author.id in notifications_list[keyword]
                in_raid = keyword in notifraid_list.keys() and message.author.id in notifraid_list[keyword]
                watchdog('Verify existence and respond accordinly')
                watchdog('In spawn: ' + str(in_spawn))
                watchdog('In raid: ' + str(in_raid))
                if int(d[0]) == bot_keywordlimit and not in_spawn and not in_raid:
                    yield from client.send_message(message.channel, "You have reached the limit of {} keywords. Delete a keyword first to add a new one.".format(bot_keywordlimit))
                else:
                    watchdog('Find keyword in list')
                    db = db_connect()
                    c = db.cursor()
                    c.execute(("SELECT * FROM notificationbot_keywords WHERE LOWER(keyword) = '{}' AND discord_id='{}'".format(keyword.lower().replace("'", "\\'"), message.author.id)))
                    row = c.fetchone()
                    c.close()
                    db_close(db)
                    watchdog('Find keyword in existing list')
                    # when keyword in file:
                    if row is not None:
                        watchdog('Updating keyword')
                        db = db_connect()
                        c = db.cursor()
                        try:
                            c.execute ("""UPDATE notificationbot_keywords SET raid=%s, spawn=%s WHERE discord_id=%s AND keyword=%s""", (raid, spawn, message.author.id, keyword.lower()))
                            db.commit()
                        except:
                            db.rollback()
                        c.close()
                        db_close(db)
                        yield from client.send_message(message.channel, 'I have updated keyword `{} [raid: {}|spawn: {}]` for you.'.format(keyword, raid, spawn))
                    else:
                        watchdog('Inserting keyword')
                        db = db_connect()
                        c = db.cursor()
                        try:
                            c.execute("""INSERT INTO notificationbot_keywords (keyword, discord_id, raid, spawn) VALUES (%s, %s, %s, %s)""", (keyword.lower(), message.author.id, int(raid), int(spawn)))
                            db.commit()
                        except MySQLdb.Error as e:
                            db.rollback()
                            watchdog(str(e))
                        c.close()
                        db_close(db)
                        notifications_list = updatedictionary()
                        notifraid_list = updateraiddictionary()
                        yield from client.send_message(message.channel, 'Added notification `{} [raid: {}|spawn: {}]`. To delete, use `!notifydel [keyword]`'.format(keyword, raid, spawn))

# !notifydel {keyword}
def if_delete(message):
    # opens file list, finds line with the keyword, deletes message.author.id from it.
    # If empty dict, delete?
    if '!notifydel' == message.content[0:10]:
        if not roleacc(message, 'user'):
            return
        msg = message.content.lower().split()
        if len(msg) < 2:
            yield from client.send_message(message.channel, "You are missing a parameter to the command, please verify and retry.")
        else:
            keyword = ""
            for x in range(1, len(msg)):
                keyword = keyword + " " + stripchars(msg[x]).strip()
            keyword = keyword.strip()
            # instance of server for later use
            server = client.get_server(discord_server)
            db = db_connect()
            c = db.cursor()
            c.execute("""DELETE FROM notificationbot_keywords WHERE LOWER(keyword)=%s AND discord_id=%s""", (keyword, message.author.id))
            deleted = c.rowcount
            db.commit()
            c.close()
            db_close(db)
            if deleted > 0:
                global notifications_list
                notifications_list = updatedictionary()
                global notifraid_list
                notifraid_list = updateraiddictionary()
                yield from client.send_message(message.channel, "Deleted keyword `{}` from the tracking.".format(keyword))
            else:
                yield from client.send_message(message.channel, "I am not tracking keyword `{}` so nothing was deleted.".format(keyword))

# !keywordcleanup
def keywords_cleanup(message):
    global roles_list
    # opens file list, finds line with the keyword, deletes message.author.id from it.
    # If empty dict, delete?
    if not roleacc(message, 'admin'):
        return
    # instance of server for later use
    server = client.get_server(discord_server)
    # build up the list of users that don't have access anymore
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT discord_id FROM notificationbot_keywords GROUP BY discord_id;")
    data = c.fetchall()
    c.close()
    db_close(db)
    cleanup = []
    for i, d in enumerate(data):
        usr = server.get_member(d[0])
        clean = True
        for role in usr.roles:
            if role.id in roles_list.keys() and (roles_list[role.id]['user'] == 1 or roles_list[role.id]['admin'] == 1):
                clean = False
        if clean:
            cleanup.append(d[0])    
    
    # Force a cleanup of the ID's found that have a role without permissions
    db = db_connect()
    c = db.cursor()    
    query = "DELETE FROM notificationbot_keywords WHERE discord_id in ({})".format(','.join(map(str,cleanup)))
    c.execute(query)
    deleted = c.rowcount
    db.commit()
    c.close()
    db_close(db)
    if deleted > 0:
        global notifications_list
        notifications_list = updatedictionary()
        global notifraid_list
        notifraid_list = updateraiddictionary()
        yield from client.send_message(message.channel, "Deleted `{}` keyword notifications from the tracking.".format(deleted))
    else:
        yield from client.send_message(message.channel, "Something went wrong cleaning up the list, make sure the database is up & running.")

# !notifications
def mynotifications(message):
    if not roleacc(message, 'user'):
        return
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT * FROM notificationbot_keywords WHERE discord_id = '{}';".format(message.author.id))
    data = c.fetchall()
    c.close()
    db_close(db)
    raid = []
    spawn = []
    for i, d in enumerate(data):
        # if raids
        if d[3] == 1:
            raid.append(d[1])
        # if spawns
        if d[4] == 1:
            spawn.append(d[1])
    notifications = "```\
    Right now I'm tracking the following information for you. Use !help to look at the commands.\n\
    Raids\n\
    " + str(raid) + "\n\
    Spawns\n\
    " + str(spawn) + "```\n"
    
    yield from client.send_message(message.channel, notifications)
    
# Helper function to update the dictionary to loop through. Lowers the DB load.
def updatedictionary():
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT keyword FROM notificationbot_keywords GROUP BY keyword, spawn HAVING spawn = 1 ORDER BY keyword;")
    data = c.fetchall()
    c.close()
    db_close(db)
    dict = {}
    for i, d in enumerate(data):
        db = db_connect()
        c = db.cursor()
        c.execute("SELECT discord_id FROM notificationbot_keywords WHERE spawn = 1 AND keyword = '{}';".format(d[0].replace("'", "\\'")))
        ids = c.fetchall()
        c.close()
        db_close(db)
        k_ids = []
        for i, id in enumerate(ids):
            k_ids.append(id[0])
        dict[d[0]] = k_ids
    return dict

# Helper function to update the dictionary to loop through. Lowers the DB load.
def updateraiddictionary():
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT keyword FROM notificationbot_keywords GROUP BY keyword, raid HAVING raid = 1 ORDER BY keyword;")
    data = c.fetchall()
    c.close()
    db_close(db)
    dict = {}
    for i, d in enumerate(data):
        db = db_connect()
        c = db.cursor()
        c.execute("SELECT discord_id FROM notificationbot_keywords WHERE raid = 1 AND keyword = '{}';".format(d[0].replace("'", "\\'")))
        ids = c.fetchall()
        c.close()
        db_close(db)
        k_ids = []
        for i, id in enumerate(ids):
            k_ids.append(id[0])
        dict[d[0]] = k_ids
    return dict
# --- End notification functions ---


# --- channel methods ---
# Function to add monitored channels to the database
def chanadd(message):
    msg = message.content.lower().split()
    if len(msg) != 2:
        yield from client.send_message(message.channel, "You are missing a parameter to the command, please verify and retry.")
    else:
        # instance of server for later use
        server = client.get_server(discord_server)
        # We expect these values.
        chanid = stripchars(msg[1])
        
        # verify existence of rol on the server
        fakechan = True
        chanfound = None
        for chan in server.channels:
            if chan.id == chanid:
                fakechan = False
                chanfound = chan
                break
        if fakechan:
            yield from client.send_message(message.channel, "The channel id you're trying to add doesn't exist, please verify and retry.")
        else:
            # See if the id exists in the database
            db = db_connect()
            c = db.cursor()
            c.execute("SELECT * FROM notificationbot_channels WHERE channel_id = '{}';".format(chanid))
            row = c.fetchone()
            c.close()
            db_close(db)
            
            # If the result exists, return
            if row is not None:
                yield from client.send_message(message.channel, "Channel `{}` already exists in the database".format(chanfound.name))
            # If the result doesn't exist, create a new entry
            else:
                db = db_connect()
                c = db.cursor()
                try:
                    c.execute("""INSERT INTO notificationbot_channels (channel_id, channel_name) VALUES (%s, %s)""", (chanfound.id, chanfound.name))
                    db.commit()
                except MySQLdb.Error as e:
                    db.rollback()
                    watchdog(str(e))
                c.close()
                db_close(db)
                global channel_list
                channel_list = chanmon()
                yield from client.send_message(message.channel, "Added channel `{}` to the database".format(chanfound.name))

# Function to delete a channel from the database
def chandel(message):
    msg = message.content.lower().split()
    if len(msg) != 2:
        yield from client.send_message(message.channel, "You are missing a parameter to the command, please verify and retry.")
    else:
        # instance of server for later use
        server = client.get_server(discord_server)
        # We expect these values.
        chanid = stripchars(msg[1])
        db = db_connect()
        c = db.cursor()
        c.execute("""DELETE FROM notificationbot_channels WHERE channel_id=%s""", (chanid,))
        deleted = c.rowcount
        db.commit()
        c.close()
        db_close(db)
        if deleted > 0:
            yield from client.send_message(message.channel, "Deleted channel with id `{}` from the database.".format(chanid))
            global channel_list
            channel_list = chanmon()
        else:
            yield from client.send_message(message.channel, "Channel with id `{}` doesn't exist in the database.".format(chanid))

# Function to list all channels in the database & if they are monitored
def chanlst(message):
    global channel_list
    msg = '```'
    msg += '-- Channels  --'.ljust(50) + 'monitored\n'
    # Get all channels from server
    server = client.get_server(discord_server)
    for chan in server.channels:
        r_mon = '[*]' if chan.id in channel_list else '[ ]'
        tmp = (chan.id + ': ' + chan.name).ljust(50) + r_mon.ljust(7) + '\n'
        if (len(tmp) + len(msg)) >  1997:
            msg += '```'
            yield from client.send_message(message.author, msg)
            msg = '```'
        msg += tmp
    msg += '```'
    yield from client.send_message(message.author, msg)

            
# Helper function to check monitored channels
def chanmon():
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT * FROM notificationbot_channels")
    data = c.fetchall()
    c.close()
    db_close(db)
    # Build a list of monitored channels
    channels = []
    for i, d in enumerate(data):
        channels.append(d[1])
    # return all monitored channels
    return channels

# --- End channel methods ---


# --- iv methods ---
# Function to add iv to the database
def ivadd(message):
    msg = message.content.lower().split()
    if len(msg) != 2:
        yield from client.send_message(message.channel, "You are missing a parameter to the command, please verify and retry.")
    else:
        global iv_list
        # instance of server for later use
        server = client.get_server(discord_server)
        # We expect these values.
        iv = int(stripchars(msg[1]))
        # See if the id exists in the database
        db = db_connect()
        c = db.cursor()
        c.execute("SELECT * FROM notificationbot_iv WHERE discord_id = '{}';".format(message.author.id))
        row = c.fetchone()
        c.close()
        db_close(db)
        
        # If the result exists, update the value.
        if row is not None:
            db = db_connect()
            c = db.cursor()
            try:
                c.execute ("""UPDATE notificationbot_iv SET iv=%s WHERE discord_id=%s""", (iv, message.author.id))
                db.commit()
            except:
                db.rollback()
            c.close()
            db_close(db)
            iv_list = updateivdictionary()
            yield from client.send_message(message.channel, "Updated IV tracking to  `{}` for you.".format(iv))
        # If the result doesn't exist, create a new entry
        else:
            db = db_connect()
            c = db.cursor()
            try:
                c.execute("""INSERT INTO notificationbot_iv (discord_id, iv) VALUES (%s, %s)""", (message.author.id, iv))
                db.commit()
            except:
                db.rollback()
            c.close()
            db_close(db)
            iv_list = updateivdictionary()
            yield from client.send_message(message.channel, "Added iv tracking `{}` for you.".format(iv))

# Function to delete a role from the database
def ivdel(message):
    old_iv  = updateivdictionary()
    # instance of server for later use
    server = client.get_server(discord_server)
    db = db_connect()
    c = db.cursor()
    c.execute("""DELETE FROM notificationbot_iv WHERE discord_id=%s""", (message.author.id,))
    deleted = c.rowcount
    db.commit()
    c.close()
    db_close(db)
    watchdog(str(deleted))
    if deleted > 0:
        global iv_list
        iv_list = updateivdictionary()
        yield from client.send_message(message.channel, "Deleted IV `{}` tracking for you.".format(old_iv[message.author.id]))
    else:
        yield from client.send_message(message.channel, "I am not tracking IV for you.")

# Function to list all IV tracking
def ivlist(message):
    global iv_list
    iv_list = updateivdictionary()
    msg = '```'
    msg += 'Name'.ljust(60) + '|IV\n'
    msg += ''.ljust(62, '-') + '\n'
    # Get all roles from server
    server = client.get_server(discord_server)
    for discord_id in iv_list.keys():
        member = server.get_member(discord_id)
        tmp = (member.name + ' (' + discord_id + ')').ljust(60) + '|' + iv_list[discord_id] + '\n'
        if (len(tmp) + len(msg)) >  1997:
            msg += '```'
            yield from client.send_message(message.author, msg)
            msg = '```'
        msg += tmp
    msg += '```'
    yield from client.send_message(message.author, msg)

# Function to list get your IV tacking
def ivinfo(message):
    global iv_list
    iv_list = updateivdictionary()
    msg = 'I am not tracking anything for you'
    # Get all roles from server
    server = client.get_server(discord_server)
    watchdog(str(iv_list))
    for discord_id in iv_list.keys():
        if discord_id == message.author.id:
            msg = 'I am currently tracking `IV {}` and above for you.'.format(iv_list[discord_id])
            break
    yield from client.send_message(message.author, msg)

# Helper function to update the IV lookup dictionary to loop through. Lowers the DB load.
def updateivdictionary():
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT * FROM notificationbot_iv;")
    data = c.fetchall()
    c.close()
    db_close(db)
    dict = {}
    for i, d in enumerate(data):
        dict[str(d[0])] = str(d[1])
    return dict

# --- End iv methods ---

# --- cp methods ---
# Function to add cp to the database
def cpadd(message):
    msg = message.content.lower().split()
    if len(msg) != 2:
        yield from client.send_message(message.channel, "You are missing a parameter to the command, please verify and retry.")
    else:
        global cp_list
        # instance of server for later use
        server = client.get_server(discord_server)
        # We expect these values.
        cp = int(stripchars(msg[1]))
        # See if the id exists in the database
        db = db_connect()
        c = db.cursor()
        c.execute("SELECT * FROM notificationbot_cp WHERE discord_id = '{}';".format(message.author.id))
        row = c.fetchone()
        c.close()
        db_close(db)
        
        # If the result exists, update the value.
        if row is not None:
            db = db_connect()
            c = db.cursor()
            try:
                c.execute ("""UPDATE notificationbot_cp SET cp=%s WHERE discord_id=%s""", (cp, message.author.id))
                db.commit()
            except:
                db.rollback()
            c.close()
            db_close(db)
            cp_list = updatecpdictionary()
            yield from client.send_message(message.channel, "Updated cp tracking to  `{}` for you.".format(cp))
        # If the result doesn't exist, create a new entry
        else:
            db = db_connect()
            c = db.cursor()
            try:
                c.execute("""INSERT INTO notificationbot_cp (discord_id, cp) VALUES (%s, %s)""", (message.author.id, cp))
                db.commit()
            except:
                db.rollback()
            c.close()
            db_close(db)
            cp_list = updatecpdictionary()
            yield from client.send_message(message.channel, "Added cp tracking `{}` for you.".format(cp))

# Function to delete a role from the database
def cpdel(message):
    old_cp  = updatecpdictionary()
    # instance of server for later use
    server = client.get_server(discord_server)
    db = db_connect()
    c = db.cursor()
    c.execute("""DELETE FROM notificationbot_cp WHERE discord_id=%s""", (message.author.id,))
    deleted = c.rowcount
    db.commit()
    c.close()
    db_close(db)
    watchdog(str(deleted))
    if deleted > 0:
        global cp_list
        cp_list = updatecpdictionary()
        yield from client.send_message(message.channel, "Deleted cp `{}` tracking for you.".format(old_cp[message.author.id]))
    else:
        yield from client.send_message(message.channel, "I am not tracking cp for you.")

# Function to list all cp tracking
def cplist(message):
    global cp_list
    cp_list = updatecpdictionary()
    msg = '```'
    msg += 'Name'.ljust(60) + '|cp\n'
    msg += ''.ljust(62, '-') + '\n'
    # Get all roles from server
    server = client.get_server(discord_server)
    for discord_id in cp_list.keys():
        member = server.get_member(discord_id)
        tmp = (member.name + ' (' + discord_id + ')').ljust(60) + '|' + cp_list[discord_id] + '\n'
        if (len(tmp) + len(msg)) >  1997:
            msg += '```'
            yield from client.send_message(message.author, msg)
            msg = '```'
        msg += tmp
    msg += '```'
    yield from client.send_message(message.author, msg)

# Function to list get your cp tacking
def cpinfo(message):
    global cp_list
    cp_list = updatecpdictionary()
    msg = 'I am not tracking anything for you'
    # Get all roles from server
    server = client.get_server(discord_server)
    watchdog(str(cp_list))
    for discord_id in cp_list.keys():
        if discord_id == message.author.id:
            msg = 'I am currently tracking `cp {}` and above for you.'.format(cp_list[discord_id])
            break
    yield from client.send_message(message.author, msg)

# Helper function to update the cp lookup dictionary to loop through. Lowers the DB load.
def updatecpdictionary():
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT * FROM notificationbot_cp;")
    data = c.fetchall()
    c.close()
    db_close(db)
    dict = {}
    for i, d in enumerate(data):
        dict[str(d[0])] = str(d[1])
    return dict

# --- End cp methods ---

# --- lvl methods ---
# Function to add lvl to the database
def lvladd(message):
    msg = message.content.lower().split()
    if len(msg) != 2:
        yield from client.send_message(message.channel, "You are missing a parameter to the command, please verify and retry.")
    else:
        global lvl_list
        # instance of server for later use
        server = client.get_server(discord_server)
        # We expect these values.
        lvl = int(stripchars(msg[1]))
        # See if the id exists in the database
        db = db_connect()
        c = db.cursor()
        c.execute("SELECT * FROM notificationbot_lvl WHERE discord_id = '{}';".format(message.author.id))
        row = c.fetchone()
        c.close()
        db_close(db)
        
        # If the result exists, update the value.
        if row is not None:
            db = db_connect()
            c = db.cursor()
            try:
                c.execute ("""UPDATE notificationbot_lvl SET lvl=%s WHERE discord_id=%s""", (lvl, message.author.id))
                db.commit()
            except:
                db.rollback()
            c.close()
            db_close(db)
            lvl_list = updatelvldictionary()
            yield from client.send_message(message.channel, "Updated lvl tracking to  `{}` for you.".format(lvl))
        # If the result doesn't exist, create a new entry
        else:
            db = db_connect()
            c = db.cursor()
            try:
                c.execute("""INSERT INTO notificationbot_lvl (discord_id, lvl) VALUES (%s, %s)""", (message.author.id, lvl))
                db.commit()
            except:
                db.rollback()
            c.close()
            db_close(db)
            lvl_list = updatelvldictionary()
            yield from client.send_message(message.channel, "Added lvl tracking `{}` for you.".format(lvl))

# Function to delete a role from the database
def lvldel(message):
    old_lvl  = updatelvldictionary()
    # instance of server for later use
    server = client.get_server(discord_server)
    db = db_connect()
    c = db.cursor()
    c.execute("""DELETE FROM notificationbot_lvl WHERE discord_id=%s""", (message.author.id,))
    deleted = c.rowcount
    db.commit()
    c.close()
    db_close(db)
    watchdog(str(deleted))
    if deleted > 0:
        global lvl_list
        lvl_list = updatelvldictionary()
        yield from client.send_message(message.channel, "Deleted lvl `{}` tracking for you.".format(old_lvl[message.author.id]))
    else:
        yield from client.send_message(message.channel, "I am not tracking lvl for you.")

# Function to list all lvl tracking
def lvllist(message):
    global lvl_list
    lvl_list = updatelvldictionary()
    msg = '```'
    msg += 'Name'.ljust(60) + '|lvl\n'
    msg += ''.ljust(62, '-') + '\n'
    # Get all roles from server
    server = client.get_server(discord_server)
    for discord_id in lvl_list.keys():
        member = server.get_member(discord_id)
        tmp = (member.name + ' (' + discord_id + ')').ljust(60) + '|' + lvl_list[discord_id] + '\n'
        if (len(tmp) + len(msg)) >  1997:
            msg += '```'
            yield from client.send_message(message.author, msg)
            msg = '```'
        msg += tmp
    msg += '```'
    yield from client.send_message(message.author, msg)

# Function to list get your lvl tacking
def lvlinfo(message):
    global lvl_list
    lvl_list = updatelvldictionary()
    msg = 'I am not tracking anything for you'
    # Get all roles from server
    server = client.get_server(discord_server)
    watchdog(str(lvl_list))
    for discord_id in lvl_list.keys():
        if discord_id == message.author.id:
            msg = 'I am currently tracking `lvl {}` and above for you.'.format(lvl_list[discord_id])
            break
    yield from client.send_message(message.author, msg)

# Helper function to update the lvl lookup dictionary to loop through. Lowers the DB load.
def updatelvldictionary():
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT * FROM notificationbot_lvl;")
    data = c.fetchall()
    c.close()
    db_close(db)
    dict = {}
    for i, d in enumerate(data):
        dict[str(d[0])] = str(d[1])
    return dict

# --- End lvl methods ---

# --- User role methods ---
# Function to add roles to the database
def roleadd(message):
    msg = message.content.lower().split()
    if len(msg) != 4:
        yield from client.send_message(message.channel, "You are missing a parameter to the command, please verify and retry.")
    else:
        # instance of server for later use
        server = client.get_server(discord_server)
        # We expect these values.
        roleid = stripchars(msg[1])
        user = int(stripchars(msg[2]))
        admin = int(stripchars(msg[3]))
        if roleid in protected_roles:
            user = 1
            admin = 1

        # verify existence of rol on the server
        fakerole = True
        rolefound = None
        for role in server.roles:
            if role.id == roleid:
                fakerole = False
                rolefound = role
                break
        if fakerole:
            yield from client.send_message(message.channel, "The role id you're trying to add doesn't exist, please verify and retry.")
        else:
            # See if the id exists in the database
            db = db_connect()
            c = db.cursor()
            c.execute("SELECT * FROM notificationbot_roles WHERE roleid = '{}';".format(roleid))
            row = c.fetchone()
            c.close()
            db_close(db)
            
            # If the result exists, update the value.
            if row is not None:
                db = db_connect()
                c = db.cursor()
                try:
                    c.execute ("""UPDATE notificationbot_roles SET user=%s, admin=%s WHERE roleid=%s""", (user, admin, roleid))
                    db.commit()
                except:
                    db.rollback()
                c.close()
                db_close(db)
                yield from client.send_message(message.channel, "Updated role `{}` to the database [admin={}, user={}]".format(rolefound.name, admin, user))
            # If the result doesn't exist, create a new entry
            else:
                db = db_connect()
                c = db.cursor()
                try:
                    c.execute("""INSERT INTO notificationbot_roles (roleid, rolename, user, admin) VALUES (%s, %s, %s,%s)""", (rolefound.id, rolefound.name, user, admin))
                    db.commit()
                except:
                    db.rollback()
                c.close()
                db_close(db)
                global roles_list
                roles_list = rolesdictionary()
                yield from client.send_message(message.channel, "Added role `{}` to the database [admin={}, user={}]".format(rolefound.name, admin, user))

# Function to delete a role from the database
def roledel(message):
    msg = message.content.lower().split()
    if len(msg) != 2:
        yield from client.send_message(message.channel, "You are missing a parameter to the command, please verify and retry.")
    else:
        # instance of server for later use
        server = client.get_server(discord_server)
        # We expect these values.
        roleid = stripchars(msg[1])
        if roleid in protected_roles:
            yield from client.send_message(message.channel, "The role with id `{}` is protected and can't be deleted.".format(roleid))
            return
        db = db_connect()
        c = db.cursor()
        c.execute("""DELETE FROM notificationbot_roles WHERE roleid=%s""", (roleid,))
        deleted = c.rowcount
        db.commit()
        c.close()
        db_close(db)
        if deleted > 0:
            global roles_list
            roles_list = rolesdictionary()
            yield from client.send_message(message.channel, "Deleted role with id `{}` from the database.".format(roleid))
        else:
            yield from client.send_message(message.channel, "Role with id `{}` doesn't exist in the database.".format(roleid))

# Function to list all roles in the database & their permissions
def rolelst(message):
    global roles_list
    roles_list = rolesdictionary()
    msg = '```'
    msg += '-- Roles  --'.ljust(50) + 'admin'.ljust(7) + 'user'.ljust(7) + 'protected\n'

    # Get all roles from server
    server = client.get_server(discord_server)
    for role in server.roles:
        in_db = role.id in roles_list.keys()
        r_ad = '[*]' if in_db and roles_list[role.id]['admin'] == 1 else '[ ]'
        r_us = '[*]' if in_db and roles_list[role.id]['user'] == 1 else '[ ]'
        r_pr = '[*]' if role.id in protected_roles else '[ ]'
        tmp = (role.id + ': ' + role.name).ljust(50) + r_ad.ljust(7) + r_us.ljust(7) + r_pr + '\n'
        if (len(tmp) + len(msg)) >  1997:
            msg += '```'
            yield from client.send_message(message.author, msg)
            msg = '```'
        msg += tmp        
    msg += '```'
    yield from client.send_message(message.author, msg)


# Helper function to check permissions
def roleacc(message, group):
    # If the user is a bot, always passthrough
    if message.author.bot or message.author.id in super_admin:
        return True
    # distinguish whether the user is high privileged than @everyone
    stopUnauth = False
    # in PM determine the user roles from the server settings.
    if message.author.__class__.__name__ ==  'User':
        msrv = client.get_server(discord_server)
        usr = msrv.get_member(message.author.id)
    # in channel message, the Member object is available directly
    elif message.author.__class__.__name__ ==  'Member':
        usr = message.author
    else:
        return stopUnauth
    try:
        getattr(usr, 'roles') 
    except AttributeError:
        msg = "-- Debug info -- \n\
        type: " + message.type.name + "\n\
        channel: " + message.channel.name + "\n\
        bot: " + str(message.author.bot) + "\n"
        watchdog(msg)
        return stopUnauth
    else:
        global roles_list
        # Cycle through the roles on the user object
        for role in usr.roles:
           if role.id in roles_list.keys() and roles_list[role.id][group] == 1:
             stopUnauth = True
             break         
        return stopUnauth
      
# Helper function to update the roles dictionary to loop through. Lowers the DB load.
def rolesdictionary():
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT * FROM notificationbot_roles")
    data = c.fetchall()
    c.close()
    db_close(db)
    # Build a dict from roles from the db
    roles = {}
    for i, d in enumerate(data):
        chunk = {}
        chunk['name'] = d[2]
        chunk['user'] = d[3]
        chunk['admin'] = d[4]
        roles[d[1]] = chunk
    # return all roles
    return roles

# --- End normal user role methods ---


# --- geolocation functions
# Helper function to locate check whether a spawn/raid falls within a radius
def geolookup(discord_id, lng, lat):
    global coord_list
    try:
        if discord_id in coord_list.keys():
            coords = coord_list[discord_id]
            u_lng = float(coords['lng'])
            u_lat = float(coords['lat'])
            u_dist = coords['km']
            distance = 6371 * 2 * math.asin(math.sqrt(math.pow(math.sin((u_lat - math.fabs(lat)) * math.pi/180 / 2),2) + math.cos(u_lat * math.pi/180 ) * math.cos(math.fabs(lat) *  math.pi/180) * math.pow(math.sin((u_lng - lng) *  math.pi/180 / 2), 2) ))
            watchdog(str(float(distance)) + " - " + str(float(u_dist)))
            return float(distance) <= float(u_dist)
        else:
            watchdog('User does not have range limitation, so let him through')
            return True
    except:
        watchdog('When the parsing has gone to shit, passthrough')
        return True

# Helper function to add geolocation limitation to the lookups
def geolocation(message):
    msg = message.content.lower().split()
    if len(msg) == 1:
        yield from client.send_message(message.channel, "You are missing a parameter to the command, please verify and retry.")
    else:
        address = ""
        limit = int(float(stripchars(msg[1])))
        for x in range(2, len(msg)):
            address += " "  + msg[x]
        address = address.strip()
        watchdog(address)
        # Get lon lat from google api.
        try:
            r = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}'.format(address, bot_gapi))
            fetch = r.json()
            lng = fetch['results'][0]['geometry']['location']['lng']
            lat = fetch['results'][0]['geometry']['location']['lat']
            watchdog(str(lng) + " " + str(lat))
        except:
            watchdog('Could not fetch coordinates from google API.')
            yield from client.send_message(message.channel, "Could not fetch coordinates from google API, make sure you didn't make any mistakes in address.")
            return
        # get the global to update.
        global coord_list

        # See if the discord_id exists in the database
        db = db_connect()
        c = db.cursor()
        c.execute("SELECT * FROM notificationbot_coord WHERE discord_id = {};".format(message.author.id))
        row = c.fetchone()
        c.close()
        db_close(db)
        
        # If the result exists, update the value.
        if row is not None:
            db = db_connect()
            c = db.cursor()
            try:
                c.execute ("""UPDATE notificationbot_coord SET lng=%s, lat=%s, km=%s WHERE discord_id=%s""", (lng, lat, limit, message.author.id))
                db.commit()
            except:
                db.rollback()
            c.close()
            db_close(db)
            coord_list = coorddictionary()
            yield from client.send_message(message.channel, "Updated range limits to `{}km` for  `{}` for you.".format(limit, address))
        # If the result doesn't exist, create a new entry
        else:
            db = db_connect()
            c = db.cursor()
            try:
                c.execute("""INSERT INTO notificationbot_coord (discord_id, lng, lat, km) VALUES (%s, %s, %s, %s)""", (message.author.id, lng, lat, limit))
                db.commit()
            except:
                db.rollback()
            c.close()
            db_close(db)
            coord_list = coorddictionary()
            yield from client.send_message(message.channel, "Added range limits `{}km` for `{}`.".format(limit,address))

# Helper function to get the stored radius & address information for a user
def geonfo(message):
    # get the global to update.
    global coord_list
    discord_id = message.author.id
    # If the result exists, update the value.
    if discord_id in coord_list.keys():
        coords = coord_list[discord_id]
        u_lng = float(coords['lng'])
        u_lat = float(coords['lat'])
        u_dist = coords['km']
        address = ""

        # Get human readable address
        try:
            r = requests.get('https://maps.googleapis.com/maps/api/geocode/json?latlng={},{}&key={}'.format(u_lat, u_lng, bot_gapi))
            fetch = r.json()
            address = fetch['results'][0]['formatted_address']
        except:
            watchdog('Could not fetch address from google API.')
            yield from client.send_message(message.channel, "Could not fetch address from google API, try again later.")
            return
        yield from client.send_message(message.channel, "Currently I am tracking keywords set in `!notifications` in a `{}km` radius from `{}`".format(u_dist, address))
    else:
        yield from client.send_message(message.channel, "You do not have any radius limitations set.")
            
# Function to delete a coordinate from the database
def geodel(message):
    db = db_connect()
    c = db.cursor()
    c.execute("""DELETE FROM notificationbot_coord WHERE discord_id=%s""", (message.author.id,))
    deleted = c.rowcount
    db.commit()
    c.close()
    db_close(db)
    if deleted > 0:
        global coord_list
        coord_list = coorddictionary()
        yield from client.send_message(message.channel, "Deleted range limitation from the database.")
    else:
        yield from client.send_message(message.channel, "There is no range limitation set for you in the database")

# Helper function to update the coord lookup dictionary to loop through. Lowers the DB load.
def coorddictionary():
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT * FROM notificationbot_coord;")
    data = c.fetchall()
    c.close()
    db_close(db)
    dict = {}
    for i, d in enumerate(data):
        coords = {}
        coords['lng'] = d[1]
        coords['lat'] = d[2]
        coords['km'] = d[3]
        dict[str(d[0])] = coords
    return dict

# --- End geolocation functions

# --- Helper Methods ---
# Helper for regex
def _regex_from_encoded_pattern(s):
    if s.startswith('/') and s.rfind('/') != 0:
        # Parse it: /PATTERN/FLAGS
        idx = s.rfind('/')
        pattern, flags_str = s[1:idx], s[idx+1:]
        flag_from_char = {
            "i": re.IGNORECASE,
            "l": re.LOCALE,
            "s": re.DOTALL,
            "m": re.MULTILINE,
            "u": re.UNICODE,
        }
        flags = 0
        for char in flags_str:
            try:
                flags |= flag_from_char[char]
            except KeyError:
                raise ValueError("unsupported regex flag: '%s' in '%s' "
                                 "(must be one of '%s')"
                                 % (char, s, ''.join(flag_from_char.keys())))
        return re.compile(s[1:idx], flags)
    else: # not an encoded regex
        return re.compile(re.escape(s))

# !botstats Helper function to print all statistics
def botstats(message):
    global roles_list
    global channel_list
    server = client.get_server(discord_server)

    # Get all channels from server
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT * FROM notificationbot_keywords;")
    data = c.fetchall()
    c.close()
    db_close(db)
    dict = {}
    raid = {}
    spawn = {}
    total_members = 0
    total_keywords = 0
    max_keywords = 0
    low_keywords = 99
    max_member = None
    low_member = None
    for i, d in enumerate(data):
        # global dict, can be used for simple stats. Will be used to calculate global statistics
        if d[2] not in dict:
            empty = []
            empty.append(d[1])
            dict[d[2]] = empty
        else:
            empty = dict[d[2]]
            empty.append(d[1])
            dict[d[2]] = empty
        # raid dict
        if d[3] == 1:
            if d[2] not in raid:
                empty = []
                empty.append(d[1])
                raid[d[2]] = empty
            else:
                empty = raid[d[2]]
                empty.append(d[1])
                raid[d[2]] = empty
        # spawn dict
        if d[4] == 1:
            if d[2] not in spawn:
                empty = []
                empty.append(d[1])
                spawn[d[2]] = empty
            else:
                empty = spawn[d[2]]
                empty.append(d[1])
                spawn[d[2]] = empty
    # Calculate stats for the bot.
    for key in dict.keys():
        usr = server.get_member(key)
        
        # build stats for total
        u_total = len(dict[key])
        total_keywords += u_total
        if u_total > max_keywords:
            max_keywords = u_total
            max_member = usr
        if u_total < low_keywords:
            low_keywords = u_total
            low_member = usr
    
    # total stats message at the top
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT keyword, count(1) cnt FROM notificationbot_keywords GROUP BY keyword order by cnt DESC LIMIT 0, 1;")
    row = c.fetchone()
    c.close()
    db_close(db)
    total_members = len(dict.keys())
    avg_keywords = total_keywords / total_members
    ost = '```'
    ost += 'Total users: ' + str(total_members) + '\n'
    ost += 'Total keywords: ' + str(total_keywords) + '\n'
    ost += 'Average keywords per users: ' + str(avg_keywords) + '\n'
    ost += 'Most keywords: ' + max_member.name + '(' + str(max_keywords) + ')\n'
    ost += 'Least keywords: ' + low_member.name + '(' + str(low_keywords) + ')\n'
    ost += 'Most common keyword: ' + row[0] + '\n'
    ost += '```'
    yield from client.send_message(message.author, ost)

    # Print raid statistics for users
    otp = '```'
    otp += 'Raid keyword statistics\n'
    otp += '\n\nuser'.ljust(50) + 'keywords\n'
    for key in raid.keys():
        usr = server.get_member(key)
        tmp = (usr.name + ' (' + key + ')').ljust(50) + str(raid[key]) + '\n'
        if (len(tmp) + len(otp)) >  1997:
            otp += '```'
            yield from client.send_message(message.author, otp)
            otp = '```'
        otp += tmp

    otp += '```'
    yield from client.send_message(message.author, otp)
    # Print spawn statistics for users
    otp = '```'
    otp += 'Spawn keyword statistics\n'
    otp += '\n\nuser'.ljust(50) + 'keywords\n'
    for key in spawn.keys():
        usr = server.get_member(key)
        tmp = (usr.name + ' (' + key + ')').ljust(50) + str(spawn[key]) + '\n'
        if (len(tmp) + len(otp)) >  1997:
            otp += '```'
            yield from client.send_message(message.author, otp)
            otp = '```'
        otp += tmp

    otp += '```'
    yield from client.send_message(message.author, otp)

# Helper function to do logging
def watchdog(message):
    if bot_debug == 1:
        date = str(datetime.datetime.now().strftime("%Y-%m-%d - %I:%M:%S"))
        f = open(os.path.join('log', str(datetime.datetime.now().strftime("%Y-%m-%d") + '-debug.log')), 'a')
        f.write(date + " # " + message + '\n')
        f.close()

# Helper function to strip unwanted characters
def stripchars(string):
    return re.sub('[{}]', '', string)

# Helper function to do autocorrect on pokemon names.
def pokemon_autocorrect(string):
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT * FROM notificationbot_levenshtein ORDER BY id;")
    data = c.fetchall()
    c.close()
    db_close(db)
    sugg = []
    for i, d in enumerate(data):
        if levenshtein(string, d[1].lower()) == 0:
            return string
        elif levenshtein(string, d[1].lower()) < 4:
            sugg.append(d[1].lower())
    return ', '.join(sugg)


# Helper function for levenshtein calculations.
def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]
    
# --- db functions ---
# Helper function to execute a query and return the results in a list object
def db_connect():
    # Setup the db connection with the global params
    connection = MySQLdb.connect(host=sql_host, port=sql_port, user=sql_user, passwd=sql_pass, db=sql_db)
    return connection
    
def db_close(connection):
    connection.close()
# --- End db functions ---
# --- End helper Methods ---


loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(client.start(discord_user, discord_pass))
    # loop.run_until_complete(client.connect())
except Exception:
    loop.run_until_complete(client.logout())
finally:
    loop.close()