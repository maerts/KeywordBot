import asyncio
import discord
import re
import datetime
import os
import traceback

## Extracts discord account info from options.txt
optionsfile = open('options.txt', 'r')
options = optionsfile.readlines()
user = options[0].rstrip()
passw = options[1].rstrip()
serverid = options[2].rstrip()

# Create dictionary from textfile.
notifications_file = open('notifications.txt', 'r+')
notifications_dict = {}
for line in notifications_file:
    linesplit = line.split()
    notifications_dict[linesplit[0]] = linesplit[1:]

client = discord.Client()

# normal users
global users_list
users_list = []
users_file = open('users.txt', 'r+')
for line in users_file:
    roleinfo = line.split(": ")
    users_list.append(roleinfo[0])
    
# admins
global admin_list
admin_list = []
admin_file = open('admins.txt', 'r+')
for line in admin_file:
    roleinfo = line.split(": ")
    admin_list.append(roleinfo[0])
    
# monitored channels
global mon_channels
mon_channels = []
channel_file = open('channels.txt', 'r+')
for line in channel_file:
    channelinfo = line.split(": ")
    mon_channels.append(channelinfo[0])
    

## Uncomment below if you want announcements on who joins the server.
@client.async_event
def on_member_join(member):
    server = member.server
    fmt = 'Welcome {0.mention} to {1.name}!'
    ##yield from client.send_message(server, fmt.format(member, server))
    ##yield from client.send_message(discord.utils.find(lambda u: u.id == member.id, client.get_all_members()), helpmsg)
    ##print('Sent intro message to '+ member.name)

@client.async_event
def on_ready():
    print('Connected! Ready to notify.')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)
    print('--Server List--')
    for server in client.servers:
        serverid = server.id
        print(server.id + ': ' + server.name)
        print('-- Roles  --'.ljust(50) + 'admin'.ljust(7) + 'user')
        for role in server.roles:
          r_ad = '[*]' if role.id in admin_list else '[ ]'
          r_us = '[*]' if role.id in users_list else '[ ]'
          print((role.id + ': ' + role.name).ljust(50) + r_ad.ljust(7) + r_us)
        print('-- Channels --'.ljust(50) + 'monitored')
        for channel in server.channels:
          c_mon = '[*]' if channel.id in mon_channels else '[ ]'
          print((channel.id + ': ' + channel.name).ljust(50) + c_mon)
        
helpmsg = "Hi I'm a notification bot!\n\
\n\
`!notification {keyword}` to add a skype-like notification\n\
`!deletenotification {keyword}` to delete it.\n\
`!notifications` for a list of your current notifications.\n\
Example: `MomoBot mentioned {keyword} in {channel-name}:` Hi {keyword}!"
  
helpamsg = "\n\n\
Admin commands\n\
\n\
`!update` to force update the notifications in the bot\n\
`!showN` print the list as it is stored in the textfile.\n\
`!showD` print the list of loaded notifications in the bot.\n\
`!channels` print all channels and which ones are monitored by me.\n\
`!chanadd {id}` add the channel with the id to the monitored list.\n\
`!chandel {id}` remove the channel from the monitored list.\n\
"
  
noaccessmsg = "Hi I'm a notification bot!\n\
\n\
Unfortunately you do not have the proper permissions to use me, read #announcements for more information on how to donate to get access."
  
@client.async_event
def on_message(message):
    if message.channel.id not in mon_channels and not message.channel.is_private:
        return
    if message.author == client.user:
        return
    if message.channel.is_private:
        if deny_access_to_func(message, 'user'):
            yield from client.send_message(message.channel, noaccessmsg)
        elif '!help' == message.content[0:5]:
            returnmsg = helpmsg
            if not deny_access_to_func(message, 'admin'):
                returnmsg += helpamsg
            yield from client.send_message(message.channel, returnmsg)

    try:
        yield from custom_notifications(message)
            
    except:
        try:
            print('Someone mentioned keyword: '+ message.content)
        except:
            print('probably some special character in message.content')
    yield from if_add(message)
    yield from if_delete(message)
    access_admin = not deny_access_to_func(message, 'admin')
    access_user = not deny_access_to_func(message, 'user')
    if '!update' == message.content[0:7] and access_admin:
        update_dict()
    elif '!showN' == message.content[0:6] and access_admin:
        yield from show(message)
    elif '!showD' == message.content[0:6] and access_admin:
        yield from showD(message)
    elif '!channels' == message.content[0:9] and access_admin:
        yield from channels(message, 'show')
    elif '!chanadd' == message.content[0:8] and access_admin:
        yield from channels(message, 'add')
    elif '!chandel' == message.content[0:8] and access_admin:
        yield from channels(message, 'del')
    elif '!chanup' == message.content[0:7] and access_admin:
        yield from channels(message, 'update')
    elif '!mynotifications' == message.content[0:16] and access_user:
        yield from mynotifications(message)
    elif '!notifications' == message.content[0:14] and access_user:
        yield from mynotifications(message)

##################################################

def custom_notifications(message):
    msglist = message.content.lower().split()
    embed = False
    if len(message.embeds) == 1:
        embed = True
        title = re.sub('[^a-zA-Z0-9 \.]', ' ', message.embeds[0]['title']).lower().split()
        desc = re.sub('[^a-zA-Z0-9 \.]', ' ', message.embeds[0]['description']).lower().split()
        msglist = msglist + title + desc
    ######
    # Loop through dictionary
    for keyword in notifications_dict:
        if keyword in msglist:
            for user_id in notifications_dict[keyword]: # if empty, does nothing
                if user_id == message.author.id:
                    print('same user')
                    pass
                elif embed:
                    try:
                        emb_title = '`[{}] was mentioned` `in #{}`'.format(keyword, message.channel.name)
                        emb_desc = str(message.embeds[0]['description'])
                        emb_url = str(message.embeds[0]['url'])
                        emb = discord.Embed(title=emb_title, description=emb_desc, url=emb_url)
                        emb.set_image(url=str(message.embeds[0]['image']['url']))
                        emb.set_thumbnail(url=str(message.embeds[0]['thumbnail']['url']))
                        yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), embed=emb)
                    except discord.DiscordException as de:
                        print(de.message)
                        yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), '`{} mentioned` **{}** `in #{}:` {}'.format('Bot', keyword, message.channel.name, str(message.embeds[0]['title'] + " - " + message.embeds[0]['url'])))
                    print('{} mentioned {} in #{}: {}'.format(message.author.name, keyword, message.channel.name, str(message.embeds[0]['title'] + " - " + message.embeds[0]['url'])))
                else:
                    yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), '`{} mentioned` **{}** `in #{}:` {}'.format(message.author.name, keyword, message.channel.name, message.content))
                    print('{} mentioned {} in #{}: {}'.format(message.author.name, keyword, message.channel.name, message.content))

# EXAMPLE: !notification apink
def if_add(message):
    # message.author.id to add to files list
    if '!notification ' == message.content[0:14]:
        if deny_access_to_func(message, 'user'):
            return
        msg = message.content.lower().split()
        notifications_file = open('notifications.txt', 'r+')
        # when keyword in file:
        keyindict = False
        if msg[1] in notifications_dict:
            keyindict = True
        
        if keyindict:
            willedit = True
            newt = '#notifications#'
            for line in notifications_file:
                linelist = line.split()
                if msg[1] == linelist[0]:
                    if message.author.id in linelist: ## check for userid
                        willedit = False

                    if willedit == True:   
                        linelist.append(message.author.id)
                        newt += '\n'
                        for element in linelist:
                            newt += element + ' '
                        newt = newt[:len(newt)-1] #gets rid of ending space
                elif line != '#notifications#\n':
                    newt += '\n' + line.strip('\n')

            if willedit:
                _rewrite(notifications_file, newt)
  
        else:
        # when keyword not in file: 
            notifications_file.read()
            notifications_file.write('\n' + msg[1] + ' ' + message.author.id)
            notifications_file.close()
            
        update_dict()
        if keyindict and not willedit:
            yield from client.send_message(message.channel, 'Notification `{}` may already be set for `{}`.'.format(msg[1], message.author.name) )
        else:
            yield from client.send_message(message.channel, 'Added notification `{}`. To delete, use `!deletenotification [keyword]`'.format(msg[1]) )

# EXAMPLE: !deletenotification apink
def if_delete(message):
    # opens file list, finds line with apink, deletes message.author.id from it.
    # If empty dict, delete?
    if '!deletenotification' == message.content[0:19]:
        if deny_access_to_func(message, 'user'):
            return
        notifications_file = open('notifications.txt', 'r+')
        msg = message.content.lower().split()
        newt = '#notifications#'
        willdelete = 0
        for line in notifications_file:
            if msg[1] == line.split()[0]: ## msg == key
                willdelete=1
                ## needs to keep the line and only delete message.author.id here, unless EMPTY
                newlist = line.split()
                try:
                    newlist.remove(message.author.id) #remove only id
                except ValueError:
                    print('ValueError')
                if not len(newlist) == 1: ## removes if no user ids left
                    newt += '\n'
                    for element in newlist:
                        newt += element + ' '
                    newt = newt[:len(newt)-1]
            elif line != '#notifications#\n':
                newt += '\n' + line.strip('\n')

        if willdelete == 1:
            _rewrite(notifications_file, newt)
            update_dict()

            yield from client.send_message(message.channel, "Deleted `{}`.".format(msg[1]) )
        else:
            yield from client.send_message(message.channel, "Couldn't find.")

# !update , used when you manually change something in the .txt
def update_dict():
    notifications_file = open('notifications.txt', 'r+')
    global notifications_dict
    notifications_dict = {}
    for line in notifications_file:
        linesplit = line.split()
        notifications_dict[linesplit[0]] = linesplit[1:]
    print('Updated.')

# !notifications
def mynotifications(message):
    global notifications_dict
    mine = []
    for keyword in notifications_dict:
        if message.author.id in notifications_dict[keyword]:
            mine.append(keyword)
    yield from client.send_message(message.channel, mine)

# !showN
def show(message):
    n = open('notifications.txt', 'r+')
    msg = '#notifications#'
    for line in n:
        if line != '#notifications#\n':
            msg += '\n' + line.strip('\n')
    yield from client.send_message(message.author, msg[:2000])
    if len(msg) >= 2000:
        #               1.1 -> 2 for math.ceil, sends extra message
        for i in range(1, math.ceil(len(msg)/2000) ):
            c1 = msg[i*2000:(i+1)*2000]
            yield from client.send_message(message.author, c1)

# !showD
def showD(message):
    global notifications_dict
    msg = ''
    for keyword in notifications_dict:
        msg += '{} {}\n'.format(keyword, notifications_dict[keyword])
    yield from client.send_message(message.author, msg[:2000])
    if len(msg) >= 2000:
        #               1 -> 2 if round returns 3, which prints 3msgs
        for i in range(1, round(len(msg)/2000) ):
            c1 = msg[i*2000:(i+1)*2000]
            yield from client.send_message(message.author, c1)

# --- channel methods ---
# !channels !chanadd !chandel !chanup
def channels(message, action):
    global mon_channels
    server = client.get_server(serverid)
    if action == 'show': # Handle the displaying of all channels and mark which ones are monitored
        msg = ''
        msg += 'active\t' + 'Channels\n'

        for channel in server.channels:
          c_mon = '[o]' if channel.id in mon_channels else '[  ]'
          msg += c_mon + '\t\t' + (channel.id + ': ' + channel.name) + '\n'
        yield from client.send_message(message.author, msg[:2000])
        if len(msg) >= 2000:
            #               1 -> 2 if round returns 3, which prints 3msgs
            for i in range(1, round(len(msg)/2000) ):
                c1 = msg[i*2000:(i+1)*2000]
                yield from client.send_message(message.author, c1)
    elif action == 'add': # Handle channel additions
        msg = message.content.lower().split()
        # Make sure the channelid exists on the server
        fakechan = True
        channelfound = None
        for channel in server.channels:
            if channel.id == msg[1]:
                fakechan = False
                channelfound = channel
                break
        if fakechan:
            yield from client.send_message(message.channel, 'Channel with id `{}` does not exist for this server.'.format(msg[1]))
            return
        # when channel in file:
        channel_file = open('channels.txt', 'r+')
        channelindict = False

        if msg[1] in mon_channels:
            channelindict = True
        
        if not channelindict:
            channel_file.read()
            channel_file.write('\n' + msg[1] + ': ' + channelfound.name)
            channel_file.close()
        # Update the channel file.
        chanup()
        if channelindict:
            yield from client.send_message(message.channel, 'Channel with id `{}` already in list.'.format(msg[1]) )
        else:
            yield from client.send_message(message.channel, 'Channel *{}* with id `{}` added. To delete, use `!channeldel [id]`'.format(channelfound.name, msg[1]) )

    elif action == 'del': # Handle deletion from the channel list
        channel_file = open('channels.txt', 'r+')
        msg = message.content.lower().split()
        willdelete = False
        channels_tmp = ""

        # cycle through the file
        for line in channel_file:
            chanfo = line.split(': ')
            # keep the file if the key doesn't match the search, if it is found, flag for rewrite
            if msg[1] != chanfo[0]:
                nl = '\n'
                if channels_tmp == '':
                    nl = ''
                channels_tmp += nl + line.strip('\n')
            else:
                willdelete = True
        
        if channels_tmp == '':
            yield from client.send_message(message.channel, 'You need at least 1 channel in this list, add another one before removing this one')

        if willdelete:
            _rewrite(channel_file, channels_tmp)
            # Update the channel file, we have to use the whole snippet because sequential function calls bug out sometimes.
            channel_file = open('channels.txt', 'r+')
            mon_channels = []
            for line in channel_file:
                channelinfo = line.split(": ")
                mon_channels.append(channelinfo[0])
            print('Channels updated.')
            yield from client.send_message(message.channel, "Channel with id `{}` no longer monitored.".format(msg[1]) )
        else:
            yield from client.send_message(message.channel, "Couldn't find channel with id `{}`.".format(msg[1]))
    elif action == 'update': # Handle the updates to the physical file on the drive
        chanup()
        yield from client.send_message(message.channel, "Channellist updated.")

def chanup():
    channel_file = open('channels.txt', 'r+')
    global mon_channels
    mon_channels = []
    for line in channel_file:
        channelinfo = line.split(": ")
        mon_channels.append(channelinfo[0])
    print('Channels updated.')

# --- End channel methods ---

# --- Helper Methods ---
            
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def _rewrite(file, newfile):
    file.truncate(0)
    file.seek(0)
    file.write(newfile)

def deny_access_to_func(message, group):
    if message.author.bot:
        return False
    # distinguish whether the user is high privileged than @everyone
    stopUnauth = True
    # in PM determine the user roles from the server settings.
    if message.author.__class__.__name__ ==  'User':
        msrv = client.get_server(serverid)
        usr = msrv.get_member(message.author.id)
    # in channel message, the Member object is available directly
    elif message.author.__class__.__name__ ==  'Member':
        usr = message.author
    else:
        return stopUnauth
        
    try:
        getattr(usr, 'roles') 
    except AttributeError:
        print("-- Debug info -- ")
        print("type: " + message.type.name)
        print("channel: " + message.channel.name)
        print("bot: " + str(message.author.bot))
        print("clean message: " + message.clean_content)
        print("message: " + message.content)
        print("system message: " + message.system_content)
        print("embeds: " + str(message.embeds))
        return stopUnauth
    else:
      if group == 'admin':
          role_list = admin_list
      elif group == 'user':
          role_list = users_list
      else:
          return False
      roles = usr.roles
      for role in roles:
         if role.id in role_list:
           stopUnauth = False
           break         
      return stopUnauth

# --- End helper Methods ---

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(client.login(user, passw))
    loop.run_until_complete(client.connect())
except Exception:
    loop.run_until_complete(client.close())
finally:
    loop.close()
