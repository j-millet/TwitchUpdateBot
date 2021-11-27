import discord
from discord.ext import commands
import requests
import json
import os
import asyncio
import time

from requests.api import get


bot = commands.Bot(command_prefix="*")
bot.remove_command('help')

with open('auth.json') as f:
    d = json.loads(f.read())
    token,client_id,client_secret = [d[x] for x in d]

async def get_oauth(cid,cs)->str:
    with open("oauth.json","r") as f:  #checks if we already have a key that is more than a day from expiry
        d = json.loads(f.read())
        if d['expiration_timestamp'] - time.time() > 24*3600: return f'Bearer {d["oauth"]}'
        
    with open("oauth.json","w") as f: #generate new auth key
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

@bot.command(name="help")
async def read_commands(ctx,*ver):
    o = "help_extra.txt" if (len(ver)>0 and ver[0]=="adv") else "help.txt"
    with open(o) as f:
        await ctx.channel.send(f.read())


print(get_oauth(client_id,client_secret))
#bot.run(token)   