import os
import json
import discord

def path(filename): #returns whole path to a file (must be in the same folder as code), needed for raspb
        return f"{os.path.dirname(__file__)}\{filename}"

def write_sub_file(guild:discord.guild,data:dict)->None:#writes data to guild file, creates file if there isn't one
    p = path(f"servers\{guild.id}subs.json")
    with open("servers.json","r+") as f:
        arr = json.loads(f.read())
        if not arr.__contains__(guild.id): arr.append(guild.id)
        f.seek(0)
        f.write(json.dumps(arr))
        f.truncate()

    with open(p,"w+") as f: 
        f.write(json.dumps(data))


def delete_sub_file(guild:discord.guild)->bool: #removes guild file
    p = path(f"servers\{guild.id}subs.json")
    if not os.path.exists(p): return False
    os.remove(p)
    return True

def access_sub_file(guild:discord.guild)->dict:  #returns guild-file data, creates file if there isn't one
    p = path(f"servers\{guild.id}subs.json")
    data = {}
    if not os.path.exists(p):
        data = {"def-channel":guild.text_channels[0].id,"subscriptions":{},"privileged":list(set([329263365858000898,guild.owner_id]))}
        write_sub_file(guild,data)
    else:
        with open(p,"r") as f:
            data = json.loads(f.read())

    return (data)
