from discord.ext import commands
import discord
from Authentication import Authentication
import GuildFileManager
import API_Calls as helix
import json

intents = discord.Intents().all()
bot = commands.Bot(command_prefix="*", intents=intents)
bot.remove_command('help')
auth = Authentication()

async def check_sub_list():
    accounts = []
    guilds = []
    with open(GuildFileManager.path("servers.json")) as f:
        guilds = json.loads(f.read())
        for guild in guilds:
            subs = GuildFileManager.access_sub_file(bot.get_guild(guild))
            accounts.extend(subs['subscriptions'].keys())

    acc_dict = dict.fromkeys(accounts,False)
    for key in acc_dict:
        acc_dict[key] = helix.is_live(key)
    
    for guild in guilds:
        g_ref = bot.get_guild(guild)
        data = GuildFileManager.access_sub_file(g_ref)
        subs = data['subscriptions']
        channel = bot.get_channel(data['def-channel'])
        for sub in subs:
            if acc_dict[sub] == True:
                if subs[sub] == False:
                    subs[sub] = True
                    await channel.send(f"https://www.twitch.tv/{sub}")
            else:
                subs[sub] = False
        data["subscriptions"] = subs
        print(data)
        GuildFileManager.write_sub_file(g_ref,data)


@bot.command(name="test")
async def test(ctx,*arg):
    await check_sub_list()

@bot.command(name="help")
async def read_commands(ctx,*ver):  #sends the contents of selected help file: help.txt for basics, help_extra.txt for commands with privileges needed
    helpfile = "help_extra.txt" if (len(ver)>0 and ver[0]=="adv") else "help.txt"
    with open(GuildFileManager.path(helpfile)) as f:
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
        if helix.user_exists(name) and (not subscriptions.__contains__(name)):
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

@bot.command(name="showpriv")
async def show_subscribers(ctx):    #sends a list of channels the server is subscribed to
    subs = GuildFileManager.access_sub_file(ctx.guild)['privileged']

    nl = '\n'
    s = f"```Privileged: {nl}{''.join([f'->{ctx.guild.get_member(x).name}{nl}' for x in subs])}```" if len(subs)>0 else "This server is not following any channel."
    await ctx.channel.send(s)



#TODO commands to add, remove privileged users
#TODO command to change def-channel


@bot.event
async def on_guild_remove(guild):
    GuildFileManager.delete_sub_file(guild)

bot.run(auth.token)
bot.wait_until_ready()