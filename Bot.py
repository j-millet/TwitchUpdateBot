from discord.ext import commands, tasks
import discord
from Authentication import Authentication
import GuildFileManager
import API_Calls as helix
import json

intents = discord.Intents().all()
bot = commands.Bot(command_prefix="*", intents=intents)
bot.remove_command('help')
auth = Authentication()

@tasks.loop(seconds=120)
async def check_sub_list():
    await bot.wait_until_ready()
    print("checking...")
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
                    await channel.send(f"Hey guys check it out!\nhttps://www.twitch.tv/{sub}\nis live!")
            else:
                subs[sub] = False
        data["subscriptions"] = subs
        GuildFileManager.write_sub_file(g_ref,data)

############################   COMMANDS    ############################

@bot.command(name="test")
async def test(ctx,*arg):
    await check_sub_list()

@bot.command(name="help")
async def help(ctx,*ver):  #sends the contents of selected help file: help.txt for basics, help_extra.txt for commands with privileges needed
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

    nl = '\n' #dunno why but I can't use backslashes in f strings lol
    s = f"```This server is following: {nl}{''.join([f'-> {x}{nl}' for x in subs])}```" if len(subs)>0 else "This server is not following any channel."
    await ctx.channel.send(s)

@bot.command(name="showpriv")
async def show_privileged(ctx):    #sends a list of the privileged users on server
    subs = GuildFileManager.access_sub_file(ctx.guild)['privileged']

    nl = '\n' #dunno why but I can't use backslashes in f strings lol
    s = f"```Privileged: {nl}{''.join([f'-> {ctx.guild.get_member(x).name}{nl}' for x in subs])}```" if len(subs)>0 else "This server is not following any channel."
    await ctx.channel.send(s)

@bot.command(name="add_priv")
async def add_privileged(ctx):
    ctx = ctx.message       #add n channels to a server's follower list
    if len(ctx.mentions) == 0: 
        await ctx.channel.send("I need names")
        return

    data = GuildFileManager.access_sub_file(ctx.guild)
    if not data['privileged'].__contains__(ctx.author.id):
        await ctx.channel.send("You don't have the privileges to do that.")
        return

    privileges = data['privileged']
    succesful,failed = [],[]
    for member in ctx.mentions:
        if not privileges.__contains__(member.id):
            privileges.append(member.id)
            succesful.append(member.name)
        else:
            failed.append(member.name)
    data["privileged"] = privileges
    GuildFileManager.write_sub_file(ctx.guild,data)

    s=""
    s += f"Succesfully added: {''.join([(x+' ') for x in succesful])}" if len(succesful) > 0 else ""
    s+= f"\nFailed to add: {''.join([(x+' ') for x in failed])}" if len(failed) > 0 else ""
    await ctx.channel.send(s)

@bot.command(name="remove_priv")
async def remove_priv(ctx):     #remove mentioned users from privileged
    ctx = ctx.message
    if len(ctx.mentions) == 0: 
        await ctx.channel.send("I need a name")
        return

    data = GuildFileManager.access_sub_file(ctx.guild)

    if (not data['privileged'].__contains__(ctx.author.id)):
        await ctx.channel.send("You don't have the privileges to do that.")
        return

    privileged = data['privileged']
    succesful,failed = [],[]
    for user in ctx.mentions:
        uid = user.id
        r = False
        if not (user == ctx.guild.owner or user == ctx.author) and privileged.__contains__(user.id):
            r = privileged.pop(privileged.index(uid)) != None
        if r: succesful.append(user.name)
        else: failed.append(user.name)
    data["privileged"] = privileged  
    GuildFileManager.write_sub_file(ctx.guild,data)

    s=""
    s += f"Succesfully removed: {''.join([(x+' ') for x in succesful])}" if len(succesful) > 0 else ""
    s+= f"\nFailed to remove: {''.join([(x+' ') for x in failed])}" if len(failed) > 0 else ""
    await ctx.channel.send(s)

@bot.command(name="change_def_channel")
async def change_def_channel(ctx):
    data = GuildFileManager.access_sub_file(ctx.guild)
    if not data['privileged'].__contains__(ctx.message.author.id):
        await ctx.channel.send("You don't have the privileges to do that.")
        return
    data['def-channel'] = ctx.channel.id
    await ctx.channel.send(f"Default notification channel changed to: {ctx.channel.name}")
    GuildFileManager.write_sub_file(ctx.guild,data)


@bot.event
async def on_guild_remove(guild): #deletes guild file if bot is kicked/banned from server
    GuildFileManager.delete_sub_file(guild)

check_sub_list.start()
bot.run(auth.token)