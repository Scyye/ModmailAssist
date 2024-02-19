import sqlite3
from datetime import datetime

import discord
from discord.ext import commands

from cogs.admin import Admin, Config

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


@bot.event
async def on_ready():
    db = sqlite3.connect("warning.sqlite")
    cursor = db.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS warns(user INTEGER, reason TEXT, time INTEGER, guild INTEGER)"
    )
    db.commit()

    await bot.add_cog(Admin(bot))

    print("Bot Notice: Bot is ready")
    try:
        synced = await bot.tree.sync()
        print(f"Bot Notice: {len(synced)} commands have been synced")
        activity = discord.Activity(name="over 1 server", type=3)
        await bot.change_presence(status=discord.Status.online, activity=activity)
    except Exception as e:
        print(e)


########################################

@bot.event
async def on_member_join(member):
    timestamp = datetime.now()
    specific_channel = bot.get_channel(Config.JoinLeave)

    embedVar = discord.Embed(
        title=f"Join | {timestamp.strftime('%I:%M %p')} UTC",
        description=
        f"{member.mention} has joined {member.guild.name}",
        colour=Config.Green)

    await specific_channel.send(embed=embedVar)


########################################


@bot.event
async def on_member_remove(member):
    timestamp = datetime.now()
    specific_channel = bot.get_channel(Config.JoinLeave)
    embedVar = discord.Embed(
        title=f"Leave | {timestamp.strftime('%I:%M %p')} UTC",
        description=
        f"{member.mention} has left {member.guild.name}",
        colour=Config.Red)
    await specific_channel.send(embed=embedVar)


bot.run('TOKEN')
