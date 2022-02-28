from unicodedata import name
from discord.ext import commands
import requests
import os
import asyncio
from Authentication import Authentication
import GuildFileManager 

def path(filename): #returns whole path to a file (must be in the same folder as code), needed for linux
    return f"{os.path.dirname(__file__)}\{filename}"

bot = commands.Bot(command_prefix="*")
bot.remove_command('help')
auth = Authentication()

def user_exists(name:str)->bool:    #check if user with name exists
    headers = {
        'Client-Id': auth.client_id,
        'Authorization': auth.get_oauth(),
    }
    params = (
        ('login', name),
    )
    response = requests.get('https://api.twitch.tv/helix/users?',headers=headers, params=params)
    return response.json()["data"] != []


def is_live(name:str)->bool: #check live status of a single channel
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
async def read_commands(ctx,*ver):  #sends the contents of selected help file: help.txt for basics, help_extra.txt for commands with privileges needed
    helpfile = "help_extra.txt" if (len(ver)>0 and ver[0]=="adv") else "help.txt"
    with open(path(helpfile)) as f:
        await ctx.channel.send(f.read())

@bot.command(name="remove")
async def remove_sub(ctx,*arg):     #remove n channels from a server's follower list
    if len(arg) == 0: 
        await ctx.channel.send("I need a channel name")
        return

    data = GuildFileManager.access_sub_file(ctx.guild)

    if not data['privileged'].__contains__(ctx.author.id):
        await ctx.channel.send("You don't have the privileges to do that.")
        return

    subscriptions = data['subscriptions']
    succesful,failed = [],[]
    for name in arg:
        name = name.lower()
        r = subscriptions.pop(name, None) != None
        if r: succesful.append(name)
        else: failed.append(name)
        data['subscriptions'] = subscriptions
    
    GuildFileManager.write_sub_file(ctx.guild,data)

    s=""
    s += f"Succesfully removed: {''.join([(x+' ') for x in succesful])}" if len(succesful) > 0 else ""
    s+= f"\nFailed to remove: {''.join([(x+' ') for x in failed])}" if len(failed) > 0 else ""
    await ctx.channel.send(s)
    
@bot.command(name="add")
async def add_sub(ctx, *arg):       #add n channels to a server's follower list
    if len(arg) == 0: 
        await ctx.channel.send("Give me a channel name")
        return

    data = GuildFileManager.access_sub_file(ctx.guild)
    if not data['privileged'].__contains__(ctx.author.id):
        await ctx.channel.send("You don't have the privileges to do that.")
        return

    subscriptions = data['subscriptions']
    succesful,failed = [],[]
    for name in arg:
        name = name.lower()
        if user_exists(name) and (not subscriptions.__contains__(name)):
            subscriptions[name] = False
            succesful.append(name)
        else:
            failed.append(name)
    
    GuildFileManager.write_sub_file(ctx.guild,data)

    s=""
    s += f"Succesfully added: {''.join([(x+' ') for x in succesful])}" if len(succesful) > 0 else ""
    s+= f"\nFailed to add: {''.join([(x+' ') for x in failed])}" if len(failed) > 0 else ""
    await ctx.channel.send(s)

@bot.command(name="showsubs")
async def show_subscribers(ctx):    #sends a list of channels the server is subscribed to
    subs = GuildFileManager.access_sub_file(ctx.guild)['subscriptions']

    nl = '\n'
    s = f"```This server is following: {nl}{''.join([f'->{x}{nl}' for x in subs])}```" if len(subs)>0 else "This server is not following any channel."
    await ctx.channel.send(s)

bot.run(auth.token)