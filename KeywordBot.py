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
passw = options[1]

# Create dictionary from textfile.
notifications_file = open('notifications.txt', 'r+')
notifications_dict = {}
for line in notifications_file:
    linesplit = line.split()
    notifications_dict[linesplit[0]] = linesplit[1:]

client = discord.Client()

## Uncomment below if you want announcements on who joins the server.
##@client.async_event
##def on_member_join(member):
##    server = member.server
##    fmt = 'Welcome {0.mention} to {1.name}!'
##    yield from client.send_message(server, fmt.format(member, server))
##    try:
##        print ( 'Welcome {0.name} to {1.name}!'.format(member,server) ) #sometimes has special char errors
##    except:
##        print ( 'Welcome specialcharsname to .reddit-kpop!')

@client.async_event
def on_ready():
    print('Connected! Ready to notify.')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)
    print('--Server List--')
    for server in client.servers:
        print(server.name)
        
@client.async_event
def on_message(message):
    if message.author == client.user:
        return
    if message.channel.is_private:
        yield from client.send_message(message.channel, "Hi I'm notification bot Momo! \n\
`!notification [keyword]` to add a skype-like notification, `!deletenotification [keyword]` to delete it.")

    try:
        yield from custom_notifications(message)
            
    except:
        try:
            print(' mentioned keyword:` '+ message.content)
        except:
            print('prob some special character in message.content')

    yield from if_add(message)
    yield from if_delete(message)
    if '!update' == message.content[0:7]:
        update_dict()
    elif '!showN' == message.content[0:6]:
        yield from show(message)


##################################################


def custom_notifications(message):
    # { 'apink' : ['id', 'id2'], 'twice' : ['id'] }
    msglist = message.content.lower().split()
    ######
    # Loop through dictionary
    for keyword in notifications_dict:
        if keyword in msglist:
            for user_id in notifications_dict[keyword]: # if empty, does nothing
                if user_id == message.author.id:
                    print('same user')
                    pass
                else:
                    yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), '`{} mentioned {} in {}:` {}'.format(message.author.name, keyword, message.channel.name, message.content))
                    print('`{} mentioned {} in {}:` {}'.format(message.author.name, keyword, message.channel.name, message.content))

# EXAMPLE: !notification apink
def if_add(message):
    # message.author.id to add to files list
    if '!notification ' == message.content[0:14]:
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

# !update , used when you change something in the .txt
def update_dict():
    notifications_file = open('notifications.txt', 'r+')
    global notifications_dict
    notifications_dict = {}
    for line in notifications_file:
        linesplit = line.split()
        notifications_dict[linesplit[0]] = linesplit[1:]
    print('Updated.')

# !shownotifications, doesn't work for some reason
def show(message):
    n = open('notifications.txt', 'r+')
    msg = '#notifications#'
    for line in n:
        if line != '#notifications#\n':
            msg += '\n' + line.strip('\n')
    yield from client.send_message(message.channel, msg)
            
############## Helper Methods ##################
            
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def _rewrite(file, newfile):
    file.truncate(0)
    file.seek(0)
    file.write(newfile)

#############################################

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(client.login(user, passw))
    loop.run_until_complete(client.connect())
except Exception:
    loop.run_until_complete(client.close())
finally:
    loop.close()
