import asyncio
import discord
import re
import datetime
import os
import configparser
import traceback
import MySQLdb

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

# Create dictionaries placeholders, on_ready they will be filled up from db.
notifications_list = {}
roles_list = {}
channel_list = []

# Start discord client
client = discord.Client()


## Uncomment below if you want announcements on who joins the server.
@client.async_event
def on_member_join(member):
    server = member.server
    fmt = 'Welcome {0.mention} to {1.name}!'
    # yield from client.send_message(server, fmt.format(member, server))
    # yield from client.send_message(discord.utils.find(lambda u: u.id == member.id, client.get_all_members()), helpmsg)
    # print('Sent intro message to '+ member.name)

@client.async_event
def on_ready():
    global notifications_list
    global channel_list
    global roles_list
    notifications_list = updatedictionary()
    channel_list = chanmon()    
    roles_list = rolesdictionary()
    print('Connected! Ready to notify.')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)
    print('--Server List--')
    for server in client.servers:
        discord_server = server.id
        print(server.id + ': ' + server.name)
        print('-- Channels --'.ljust(50) + 'monitored')
        for channel in server.channels:
          c_mon = '[*]' if channel.id in channel_list else '[ ]'
          print((channel.id + ': ' + channel.name).ljust(50) + c_mon)
    

# --- Help messages ---
# The !help message for normal users
helpmsg = "Hi I'm a notification bot!\n\
\n\
`!notify {keyword}` to add a skype-like notification\n\
`!notifydel {keyword}` to delete it.\n\
`!notifications` for a list of your current notifications.\n\
Example: `MomoBot mentioned {keyword} in {channel-name}:` Hi {keyword}!"

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
"
# The message shown for unprivileged users
noaccessmsg = "Hi I'm a notification bot!\n\
\n\
Unfortunately you do not have the proper permissions to use me, read #announcements for more information on how to donate to get access."
# --- End help messages ---

@client.async_event
def on_message(message):
    global notifications_list
    global channel_list
    if message.channel.id not in channel_list and not message.channel.is_private:
        return
    if message.author == client.user:
        return
    if message.channel.is_private:
        if not roleacc(message, 'user'):
            yield from client.send_message(message.channel, noaccessmsg)
        elif '!help' == message.content[0:5]:
            returnmsg = helpmsg
            if roleacc(message, 'admin'):
                returnmsg += helpamsg
            yield from client.send_message(message.channel, returnmsg)

    # Handle incoming messages and filter them for keywords.
    try:
        yield from custom_notifications(message)
            
    except:
        try:
            print('Someone mentioned keyword: '+ message.content)
        except:
            print('probably some special character in message.content')
    yield from if_add(message)
    yield from if_delete(message)
    access_admin = roleacc(message, 'admin')
    access_user = roleacc(message, 'user')
    if '!update' == message.content[0:7] and access_admin:
        notifications_list = updatedictionary()
    elif '!chanlst' == message.content[0:8] and access_admin:
        yield from chanlst(message)
    elif '!chanadd' == message.content[0:8] and access_admin:
        yield from chanadd(message)
    elif '!chandel' == message.content[0:8] and access_admin:
        yield from chandel(message)
    elif '!roleadd' == message.content[0:8] and access_admin:
        yield from roleadd(message)
    elif '!roledel' == message.content[0:8] and access_admin:
        yield from roledel(message)
    elif '!rolelst' == message.content[0:8] and access_admin:
        yield from rolelst(message)
    elif '!keywordcleanup' == message.content[0:15] and access_admin:
        yield from keywords_cleanup(message)
    elif '!notifications' == message.content[0:14] and access_user:
        yield from mynotifications(message)

##################################################


# --- notification functions ---
# General catch all for all speech to pick up on keywords.
def custom_notifications(message):
    global roles_list
    global notifications_list
    server = client.get_server(discord_server)
    if message.channel.name == None:
        return
    msglist = message.content.lower().split()
    embed = False
    if len(message.embeds) == 1:
        embed = True
        title = re.sub('[^a-zA-Z0-9 \.]', ' ', message.embeds[0]['title']).lower().split()
        desc = re.sub('[^a-zA-Z0-9 \.]', ' ', message.embeds[0]['description']).lower().split()
        msglist = msglist + title + desc
    ######
    # Loop through dictionary
    for keyword in notifications_list.keys():
        if keyword in msglist:
            for user_id in notifications_list[keyword]: # if empty, does nothing
                # Make sure we don't notify users whose access has been revoked
                usr = server.get_member(user_id)
                revoke = True
                for role in usr.roles:
                    if role.id in roles_list.keys() and roles_list[role.id]['user'] == 1:
                        revoke = False
                        break
                if user_id == message.author.id or revoke:
                    print('Invalid user: same user or role with access revoked')
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
                        print(str(de.message))
                        yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), '`{} mentioned` **{}** `in #{}:` {}'.format('Bot', keyword, message.channel.name, str(message.embeds[0]['title'] + " - " + message.embeds[0]['url'])))
                    print('{} mentioned {} in #{}: {}'.format(message.author.name, keyword, message.channel.name, str(message.embeds[0]['title'] + " - " + message.embeds[0]['url'])))
                else:
                    yield from client.send_message(discord.utils.find(lambda u: u.id == user_id, client.get_all_members()), '`{} mentioned` **{}** `in #{}:` {}'.format(message.author.name, keyword, message.channel.name, message.content))
                    print('{} mentioned {} in #{}: {}'.format(message.author.name, keyword, message.channel.name, message.content))


# !notify {keyword}
def if_add(message):
    # message.author.id to add to files list
    if '!notify ' == message.content[0:8]:
        if not roleacc(message, 'user'):
            return
        msg = message.content.lower().split()
        if len(msg) != 2:
            yield from client.send_message(message.channel, "You are missing a parameter for the command, please verify and retry.")
        else:
          keyword = msg[1]

          db = db_connect()
          c = db.cursor()
          c.execute("SELECT * FROM notificationbot_keywords WHERE LOWER(keyword) = LOWER('{}') AND discord_id = '{}';".format(keyword, message.author.id))
          row = c.fetchone()
          c.close()
          db_close(db)
          # when keyword in file:
          if row is not None:
              yield from client.send_message(message.channel, 'I am already tracking `{}` for you.'.format(keyword))
          else:
              db = db_connect()
              c = db.cursor()
              try:
                  c.execute("""INSERT INTO notificationbot_keywords (keyword, discord_id) VALUES (%s, %s)""", (keyword.lower(), message.author.id))
                  db.commit()
              except MySQLdb.Error as e:
                  db.rollback()
                  print(str(e))

              db_close(db)
              global notifications_list
              notifications_list = updatedictionary()
              yield from client.send_message(message.channel, 'Added notification `{}`. To delete, use `!notifydel [keyword]`'.format(keyword))

            
# !notifydel {keyword}
def if_delete(message):
    # opens file list, finds line with the keyword, deletes message.author.id from it.
    # If empty dict, delete?
    if '!notifydel' == message.content[0:10]:
        if not roleacc(message, 'user'):
            return
        msg = message.content.lower().split()
        if len(msg) != 2:
            yield from client.send_message(message.channel, "You are missing a parameter to the command, please verify and retry.")
        else:
            keyword = msg[1]
            # instance of server for later use
            server = client.get_server(discord_server)
            # We expect these values.
            chanid = msg[1]
            db = db_connect()
            c = db.cursor()
            c.execute("""DELETE FROM notificationbot_keywords WHERE LOWER(keyword)=%s AND discord_id=%s""", (keyword, message.author.id))
            deleted = c.rowcount
            db.commit()
            db_close(db)
            if deleted > 0:
                global notifications_list
                notifications_list = updatedictionary()
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
    db_close(db)
    if deleted > 0:
        global notifications_list
        notifications_list = updatedictionary()
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
    mine = []
    for i, d in enumerate(data):
        mine.append(d[1])
    yield from client.send_message(message.channel, mine)

# Helper function to update the dictionary to loop through. Lowers the DB load.
def updatedictionary():
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT keyword FROM notificationbot_keywords GROUP BY keyword ORDER BY keyword;")
    data = c.fetchall()
    c.close()
    db_close(db)
    dict = {}
    for i, d in enumerate(data):
        db = db_connect()
        c = db.cursor()
        c.execute("SELECT discord_id FROM notificationbot_keywords WHERE keyword = '{}';".format(d[0]))
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
        chanid = msg[1]
        
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
                    print(str(e))

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
        chanid = msg[1]
        db = db_connect()
        c = db.cursor()
        c.execute("""DELETE FROM notificationbot_channels WHERE channel_id=%s""", (chanid,))
        deleted = c.rowcount
        db.commit()
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
    db = db_connect()
    c = db.cursor()
    c.execute("SELECT * FROM notificationbot_channels")
    data = c.fetchall()
    c.close()
    db_close(db)

    msg = '```'
    msg += '-- Channels  --'.ljust(50) + 'monitored\n'
    # Get all channels from server
    server = client.get_server(discord_server)
    for chan in server.channels:
        r_mon = '[*]' if chan.id in channel_list else '[ ]'

        msg += (chan.id + ': ' + chan.name).ljust(50) + r_mon.ljust(7) + '\n'
    msg += '```'
    yield from client.send_message(message.author, msg[:2000])
    if len(msg) >= 2000:
        for i in range(1, round(len(msg)/2000) ):
            c1 = msg[i*2000:(i+1)*2000]
            yield from client.send_message(message.author, c1)
            
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
        roleid = msg[1]
        user = int(msg[2])
        admin = int(msg[3])
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
        roleid = msg[1]
        if roleid in protected_roles:
            yield from client.send_message(message.channel, "The role with id `{}` is protected and can't be deleted.".format(roleid))
            return
        db = db_connect()
        c = db.cursor()
        c.execute("""DELETE FROM notificationbot_roles WHERE roleid=%s""", (roleid,))
        deleted = c.rowcount
        db.commit()
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
        msg += (role.id + ': ' + role.name).ljust(50) + r_ad.ljust(7) + r_us.ljust(7) + r_pr + '\n'
    msg += '```'
    yield from client.send_message(message.author, msg[:2000])
    if len(msg) >= 2000:
        for i in range(1, round(len(msg)/2000) ):
            c1 = msg[i*2000:(i+1)*2000]
            yield from client.send_message(message.author, c1)

# Helper function to check permissions
def roleacc(message, group):
    # If the user is a bot, always passthrough
    if message.author.bot:
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
        print("-- Debug info -- ")
        print("type: " + message.type.name)
        print("channel: " + message.channel.name)
        print("bot: " + str(message.author.bot))
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

# --- Helper Methods ---
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
    loop.run_until_complete(client.login(discord_user, discord_pass))
    loop.run_until_complete(client.connect())
except Exception:
    loop.run_until_complete(client.close())
finally:
    loop.close()
