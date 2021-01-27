import discord
import os

from datetime import datetime
from pytz import timezone
from discord.ext import commands
from dotenv import load_dotenv
from io import BytesIO

from storage import retrieve_conf_channel, retrieve_log_channel, add_confessions_channel, add_log_channel, remove_log_channel
from storage import is_blocked, hash_and_store_user, block_user, allow_user

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

tz = timezone('US/Eastern')

intents = discord.Intents.default()
intents.members = True

help_command = commands.DefaultHelpCommand(no_category="Commands", verify_checks=False)

game = discord.Game("dm !conf <server id>")

bot = commands.Bot(command_prefix='!', intents=intents, help_command=help_command, activity=game)
channel_map = dict()

@bot.command(usage="<server id> <message>", help="confess server id and message to the bot to send an anonymous message. dm only.",
	brief="dm the bot a server id and confession")
@commands.dm_only()
async def conf(ctx, *, message=''):
	print(message)
	if len(message) != 0 or ctx.message.attachments != []:

		# parse the message ourselves, since we just want to take in the whole message as is
		message = message.split(' ', 1)
		guild_id = message[0]

		# the message might be empty, with an image
		if len(message) == 1 and ctx.message.attachments != []:
			message = ""
		elif len(message) == 1:
			await ctx.send('Can\'t send a blank confession!')
			return
		else:
			message = message[1]

		# verify that this is a valid guild
		try:
			guild_id = int(guild_id)
		except ValueError:
			await ctx.send('Invalid server id.')
			return

		# verify that there is a channel for this guild
		try:
			channel_id = retrieve_conf_channel(guild_id)
		except KeyError:
			await ctx.send('This guild is not configured with confessions++ yet.')
			return
		
		# checks to perform: is the bot in the guild and is the user in the guild
		# might be able to eliminate the first check, because of how k v pairs are stored
		guild = bot.get_guild(guild_id)
		if guild is None:
			await ctx.send('This bot is not in that server.')
			return
		else:
			user_id = ctx.message.author.id
			member = guild.get_member(user_id)
			if member is None:
				await ctx.send('You are not in that server!')
				return

		# we need to check if the user is allowed to use confessions in that server
		if is_blocked(user_id, guild.id):
			await ctx.send("You are blocked from confessions in that server!")
			return

		# now we can send the message (hopefully)
		now = datetime.now(tz)
		# current_time = now.strftime("%m/%d %H:%M")

		# make message into embed
		embed = discord.Embed(description=message)
		embed.timestamp = now

		# add image attatchments to the file
		files = []
		for file in ctx.message.attachments:
			fp = BytesIO()
			await file.save(fp)
			files.append(discord.File(fp, filename=file.filename, spoiler=file.is_spoiler()))
			imageURL = ctx.message.attachments[0].url
			embed.set_image(url=imageURL)

		channel = bot.get_channel(channel_id)
		# note: this should never happen, check should go through in the set function
		if channel is None:
			await ctx.send('This channel does not exist')

		my_message = await channel.send(embed=embed)

		# log the confession if the channel set up
		try:
			log_channel_id = retrieve_log_channel(guild_id)
		except KeyError:
			pass
		else:
			log_msg = ctx.message.author.mention + ': ' + message
			log_embed = discord.Embed(description=log_msg)
			log_embed.set_author(name="Confession by " + str(ctx.message.author), icon_url=ctx.message.author.avatar_url)
			footer = 'user id: ' + str(user_id)
			log_embed.set_footer(text=footer)
			log_embed.timestamp = now
			log_channel = guild.get_channel(log_channel_id)

			await log_channel.send(embed=log_embed)

		await ctx.send('Your message has been sent to ' + guild.name)

		hash_and_store_user(my_message.id, ctx.message.author.id, guild_id)


@bot.command(help="use in a channel to set it as the confessions channel", brief="sets confessions channel")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def set(ctx):
	channel_id = ctx.channel.id
	guild_id = ctx.guild.id

	# do the redis/postgres shit here.. dict for now
	add_confessions_channel(guild_id, channel_id)
	await ctx.send('Added ' + ctx.channel.name + ' as the confessions channel for ' + ctx.guild.name)


@bot.command(help="use in a channel to set it as the logging channel", brief="sets logging channel")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def log(ctx):
	channel_id = ctx.channel.id
	guild_id = ctx.guild.id

	add_log_channel(guild_id, channel_id)
	await ctx.send('Added ' + ctx.channel.name + ' as the log channel for ' + ctx.guild.name)

@bot.command(help="use in a channel to remove logging channel", brief="disables logs")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def rmlog(ctx):
	guild_id = ctx.guild.id
	try:
		remove_log_channel(guild_id)
	except KeyError:
		await ctx.send('No logging channel to remove!')
	else:
		await ctx.send('Logs have been removed.')


@bot.command(help="use with a message id to prevent its sender from confessing in this server", brief="bans for this server")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def block(ctx, message_id):
	try:
		block_user(message_id)
	except KeyError:
		await ctx.send('This message is not available.')
	else:
		await ctx.send('User blocked from using confessions on this server.')


@bot.command(help="use with a message to allow its sender to confess in this server again", brief="unblocks for this server")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def allow(ctx, message_id):
	try:
		allow_user(message_id)
	except KeyError:
		await ctx.send('That user is not blocked!')
	else:
		await ctx.send('User has been unblocked.')


@bot.command(help="use to check if log channel exists", brief="checks if logs")
@commands.guild_only()
async def logexists(ctx):
	try:
		retrieve_log_channel(ctx.guild.id)
	except KeyError:
		await ctx.send("no logs configured")
	else:
		await ctx.send("logs have been configured")


bot.run(BOT_TOKEN)