import discord
from discord.ext import commands
import requests
import json
import os
import asyncio


bot = commands.Bot(command_prefix="*")
bot.remove_command('help')

with open('auth.json') as f:
    d = json.loads(f.read())
    token,client_id,client_secret = [d[x] for x in d]

@bot.command(name="help")
async def read_commands(ctx,*ver):
    o = "help_extra.txt" if (len(ver)>0 and ver[0]=="adv") else "help.txt"
    with open(o) as f:
        await ctx.channel.send(f.read())


        
bot.run(token)   