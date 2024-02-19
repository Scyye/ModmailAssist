import sqlite3
from datetime import datetime, timedelta

import discord
from discord import Embed, User
from discord.ext import commands
from discord.ext.commands import Context


class Config:
    LogChannel = 1208425715767185438
    BotStatus = 1208426018788876318
    JoinLeave = 1208426209113804870
    Green = 0x57f287
    WarningColour = 0xfee75c
    MuteColour = 0xffa500
    Red = 0xed4245


async def check(ctx: Context):
    if not ctx.author.guild_permissions.administrator:
        await ctx.reply(embed=create_embed("Missing Permissions",
                                           "You do not have Administrator permissions in this server; hence you are "
                                           "unable to use this command.",
                                           Config.Red),
                        ephemeral=True)
        return False
    return True


def create_embed(title, description, color=Config.Green):
    return discord.Embed(title=title, description=description, color=color)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_embed(self, ctx: Context, title, description, color=Config.Green):
        embed = create_embed(title, description, color)
        await ctx.reply(embed=embed, ephemeral=True)

    async def send_dm(self, member: discord.Member, embed: Embed):
        try:
            await member.send(embed=embed)
            return True
        except discord.Forbidden:
            return False

    @commands.hybrid_command(name="warn", description="Warn a member in the server")
    async def warn(self, ctx: Context, member: discord.Member, *, reason: str = "No reason provided"):
        if not await check(ctx):
            return

        timestamp = datetime.now()
        db = sqlite3.connect("warning.sqlite")
        cursor = db.cursor()

        cursor.execute("INSERT INTO warns (user, reason, time, guild) VALUES (?, ?, ?, ?)",
                       (member.id, reason, int(datetime.now().timestamp()), ctx.guild.id))
        db.commit()

        cursor.execute("SELECT * FROM warns WHERE user = ? AND guild = ?", (member.id, ctx.guild.id))
        warnings = len(cursor.fetchall())

        await self.send_embed(ctx, "Success!",
                              f"You have successfully warned {member.mention}. They now have {warnings} warnings.")

        log = create_embed(
            title=f"Member Warned | {timestamp.strftime('%I:%M %p')} UTC",
            description=f"**Member Warned:** {member.mention}\n**Warning Number:** {warnings}\n"
                        f"**Moderator:** {ctx.author.mention}",
            color=Config.WarningColour
        )
        await ctx.bot.get_channel(Config.LogChannel).send(embed=log)
        await self.send_dm(member, log)

    @commands.hybrid_command(name="removewarning", description="Remove a member's warning in the server")
    async def removewarn(self, ctx: Context, member: discord.Member):
        if not check(ctx):
            return

        db = sqlite3.connect("warning.sqlite")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM warns WHERE user = ? AND guild = ?", (member.id, ctx.guild.id))
        data = cursor.fetchone()
        if data:
            cursor.execute("DELETE FROM warns WHERE user = ? AND guild = ?", (member.id, ctx.guild.id))
            await self.send_embed(ctx, "Success!", f"You have successfully removed 1 warning from {member.mention}.")

    async def moderation_action(self, ctx: Context, action: str, member: discord.Member, reason: str, color, dm_message):
        if not check(ctx):
            return

        timestamp = datetime.now()
        embed = create_embed(
            title=f"Member {action} | {timestamp.strftime('%I:%M %p')} UTC",
            description=f"**Member {action}:** {member.mention}\n**Reason for {action}:** {reason}\n**Moderator:** {ctx.author.mention}",
            color=color
        )

        await self.send_embed(ctx, "Success!",
                              f"You have successfully {action.lower()} the user {member.mention} for the following reason: {reason}")

        await ctx.bot.get_channel(Config.LogChannel).send(embed=embed)
        await self.send_dm(member, embed)

    @commands.hybrid_command(name="kick", description="Kick a member from the server")
    async def kick(self, ctx: Context, member: discord.Member, *, reason: str = "No reason provided"):
        await self.moderation_action(ctx, "Kicked", member, reason, Config.WarningColour,
                                     f"You have been kicked from **{ctx.guild.name}** for the following reason: {reason}. You were kicked by {ctx.author.name}, who is a moderator.")

    @commands.hybrid_command(name="mute", description="Mute a member from the server")
    async def mute(self, ctx: Context, member: discord.Member, seconds: int = 0, minutes: int = 0, hours: int = 0,
                    days: int = 0, *, reason: str = "No reason provided"):
        if not check(ctx):
            return

        duration = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        await member.timeout(duration, reason=reason)

        await self.send_embed(ctx, "Success!",
                              f"You have successfully muted the user {member.mention} for {duration} for the following reason: {reason}")

        timestamp = datetime.now()
        embedLog = create_embed(
            title=f"Member Muted | {timestamp.strftime('%I:%M %p')} UTC",
            description=(
                f"**Member Muted:** {member.mention}\n"
                f"**Reason for Mute:** {reason}\n"
                f"**Duration:** {duration}\n"
                f"**Moderator:** {ctx.author.mention}"
            ),
            color=Config.MuteColour
        )

        await ctx.bot.get_channel(Config.LogChannel).send(embed=embedLog)
        await self.send_dm(member, embedLog)

    @commands.hybrid_command(name="ban", description="Ban a member from your server")
    async def ban(self, ctx: Context, user: User, *, reason: str = "No reason provided"):
        if not check(ctx):
            return


    async def ban(self, ctx: Context, user: User, *, reason: str = "No reason provided"):
        if not check(ctx):
            return

        timestamp = datetime.now()
        embedLog = discord.Embed(
            title=f"Member Banned | {timestamp.strftime('%I:%M %p')} UTC",
            description=(
                f"**Member Banned:** {user.mention}\n"
                f"**Reason for Ban:** {reason}\n"
                f"**Moderator:** {ctx.author.mention}"
            ),
            colour=Config.Red
        )

        embedUser = discord.Embed(
            title=f"Server Ban | {timestamp.strftime('%I:%M %p')} UTC",
            description=(
                f"You have been banned from **{ctx.guild.name}** due to the following reason: {reason}. "
                f"You were banned by {ctx.author.name}, who is a moderator."
            ),
            colour=Config.Red
        )

        await ctx.reply(embed=self.embed_secret, ephemeral=True)
        specific_channel = self.bot.get_channel(Config.LogChannel)
        await specific_channel.send(embed=embedLog)

        try:
            if user.dm_channel and user.dm_channel.permissions_for(user).read_messages:
                await user.dm_channel.send(embed=embedUser)
            else:
                await user.send(embed=embedUser)
        except discord.Forbidden:
            print("Unable to send message to user.")

        await ctx.guild.ban(user, reason=reason)

    @commands.hybrid_command(name="unban", description="Unban a member from your server")
    async def unban(self, ctx: Context, user: User, *, reason: str = "No reason provided"):
        if not check(ctx):
            return

        timestamp = datetime.now()
        embedLog = discord.Embed(
            title=f"Member Unbanned | {timestamp.strftime('%I:%M %p')} UTC",
            description=(
                f"**Member Unbanned:** {user.mention}\n"
                f"**Reason for Unban:** {reason}\n"
                f"**Moderator:** {ctx.author.mention}"
            ),
            colour=Config.Green
        )

        embedUser = discord.Embed(
            title=f"Server Unban | {timestamp.strftime('%I:%M %p')} UTC",
            description=(
                f"You have been unbanned from **{ctx.guild.name}** due to the following reason: {reason}. "
                f"You were unbanned by {ctx.author.name}, who is a moderator."
            ),
            colour=Config.Green
        )

        specific_channel = self.bot.get_channel(Config.LogChannel)

        try:
            ban = await ctx.guild.fetch_ban(user)
            await ctx.guild.unban(user, reason=reason)
            await specific_channel.send(embed=embedLog)
            await self.send_dm(user, embedUser)
        except discord.NotFound:
            await self.send_embed(ctx, "Error",
                                  f"According to our systems, {user.mention} is not currently banned from {ctx.guild.name}. Hence, we are unable to unban this user at this time.",
                                  Config.Red)
        except Exception:
            await self.send_embed(ctx, "Error",
                                  f"For an unknown reason, we are currently unable to unban {user.mention} from {ctx.guild.name}. "
                                  "Please report this issue using the ModMail bot, and ask to speak to mv4ddy.",
                                  Config.Red)
