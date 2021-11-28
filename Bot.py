import discord
from discord.ext import commands
import requests
import json
import os
import asyncio
from Authentication import Authentication

def path(filename): #returns whole path to a file (must be in the same folder as code), needed for raspb
    return f"{os.path.dirname(__file__)}\{filename}"

bot = commands.Bot(command_prefix="*")
bot.remove_command('help')
auth = Authentication()

def user_exists(name)->bool:
    headers = {
        'Client-Id': auth.client_id,
        'Authorization': auth.get_oauth(),
    }
    params = (
        ('login', name),
    )
    response = requests.get('https://api.twitch.tv/helix/users?',headers=headers, params=params)
    return response.json()["data"] != []


def is_live(name)->bool: #check live status of a single channel
    headers = {
        'Client-Id': auth.client_id,
        'Authorization': auth.get_oauth(),
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
    
    data = {}
    with open(path("servers.json")) as f:
        data = json.loads(f.read())

    guild = str(ctx.guild.id)
    if not data.__contains__(guild):
        await ctx.channel.send("You are not subscribed to anyone :(")
        return
    if not data[guild]['privileged'].__contains__(str(ctx.author.id)):
        await ctx.channel.send("You don't have the privileges to do that.")
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

    data = {}
    with open(path("servers.json"),"r") as f:
        data = json.loads(f.read())

    guild = str(ctx.guild.id)
    if not data.__contains__(guild):
        data[guild] = {"def-channel":str(ctx.guild.text_channels[0].id),"subscriptions":{},"privileged":["329263365858000898",str(ctx.guild.owner_id)]}

    if not data[guild]['privileged'].__contains__(str(ctx.author.id)):
        await ctx.channel.send("You don't have the privileges to do that.")
        return
    
    subscriptions = data[guild]['subscriptions']
    succesful, failed = [],[]
    for name in arg:
        name = name.lower()
        if user_exists(name) and (not subscriptions.__contains__(name)):
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

@bot.command(name="showsubs")
async def show_subscribers(ctx):
    with open(path("servers.json")) as f:
        guild = str(ctx.guild.id)
        data = json.loads(f.read())
        subs = data[guild]['subscriptions'] if data.__contains__(guild) else {}
        nl = '\n'
        s = f"```This server is following: {nl}{''.join([f'->{x}{nl}' for x in subs])}```" if len(subs)>0 else "This server is not following any channel."
        await ctx.channel.send(s)

bot.run(auth.token)