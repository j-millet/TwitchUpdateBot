import discord
from discord.ext import commands
import requests
import json
import os
import asyncio
import time

def path(filename): #returns whole path to a file (must be in the same folder as code), needed for raspb
    return f"{os.path.dirname(__file__)}\{filename}"

bot = commands.Bot(command_prefix="*")
bot.remove_command('help')

with open(path('auth.json')) as f: #read tokens and other auth from file
    d = json.loads(f.read())
    token,client_id,client_secret = [d[x] for x in d]


def get_oauth(cid,cs)->str: #returns an OAuth key for helix api authorization -> "Bearer xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    with open(path("oauth.json"),"r") as f:  #checks if we already have a key that is more than a day from expiry
        d = json.loads(f.read())
        if d['expiration_timestamp'] - time.time() > 24*3600: return f'Bearer {d["oauth"]}'
        
    with open(path("oauth.json"),"w") as f: #generate new auth key
        d = {}
        data={
            "client_id":cid,
            "client_secret":cs,
            "grant_type":"client_credentials"
        }
        r = requests.post("https://id.twitch.tv/oauth2/token",data=data)
        d['expiration_timestamp'] = (time.time()+r.json()['expires_in'])
        d['oauth'] = r.json()["access_token"]
        f.write(json.dumps(d))
        return f'Bearer {d["oauth"]}'


def user_exists(name,cid,cs)->bool:
    headers = {
        'Client-Id': cid,
        'Authorization': get_oauth(cid,cs),
    }
    params = (
        ('login', name),
    )
    response = requests.get('https://api.twitch.tv/helix/users?',headers=headers, params=params)
    return response.json()["data"] != []


def is_live(name, cid,cs)->bool: #check live status of a single channel
    headers = {
        'Client-Id': cid,
        'Authorization': get_oauth(cid,cs),
    }
    params = (
        ('user_login', name),
    )
    response = requests.get('https://api.twitch.tv/helix/streams?',headers=headers, params=params)
    return response.json()['data'] != []


@bot.command(name="help")
async def read_commands(ctx,*ver):
    o = "help_extra.txt" if (len(ver)>0 and ver[0]=="adv") else "help.txt"
    with open(path(o)) as f:
        await ctx.channel.send(f.read())


@bot.command(name="remove")
async def remove_sub(ctx,*arg):     #remove n channels from a server's follower list
    if len(arg) == 0: 
        await ctx.channel.send("I need a channel name")
        return
    
    guild = str(ctx.guild.id)
    data = {}

    with open(path("servers.json")) as f:
        data = json.loads(f.read())

    if not data.__contains__(guild):
        await ctx.channel.send("You are not subscribed to anyone :(")
        return
    subscriptions = data[guild]['subscriptions']
    succesful,failed = [],[]
    for name in arg:
        name = name.lower()
        r = subscriptions.pop(name, None) != None
        if r: succesful.append(name)
        else: failed.append(name)
        data[guild]['subscriptions'] = subscriptions
    
    with open(path("servers.json"),"w") as f:
        f.write(json.dumps(data))
        s=""
        s += f"Succesfully removed: {''.join([(x+' ') for x in succesful])}" if len(succesful) > 0 else ""
        s+= f"\nFailed to remove: {''.join([(x+' ') for x in failed])}" if len(failed) > 0 else ""
        await ctx.channel.send(s)


@bot.command(name="add")
async def add_sub(ctx, *arg):       #add n channels to a server's follower list
    if len(arg) == 0: 
        await ctx.channel.send("Give me a channel name")
        return

    global client_id,client_secret
    data = {}
    guild  = str(ctx.guild.id)

    with open(path("servers.json"),"r") as f:
        data = json.loads(f.read())

    if not data.__contains__(guild):
        data[guild] = {"def-channel":str(ctx.guild.text_channels[0].id),"subscriptions":{},"privileged":["329263365858000898",str(ctx.guild.owner_id)]}

    subscriptions = data[guild]['subscriptions']
    succesful, failed = [],[]
    for name in arg:
        name = name.lower()
        if user_exists(name,client_id,client_secret) and (not subscriptions.__contains__(name)):
            subscriptions[name] = False
            succesful.append(name)
        else:
            failed.append(name)

    data[guild]['subscriptions'] = subscriptions
    with open(path("servers.json"),"w") as f:
        f.write(json.dumps(data))
        s=""
        s += f"Succesfully added: {''.join([(x+' ') for x in succesful])}" if len(succesful) > 0 else ""
        s+= f"\nFailed to add: {''.join([(x+' ') for x in failed])}" if len(failed) > 0 else ""
        await ctx.channel.send(s)

bot.run(token)