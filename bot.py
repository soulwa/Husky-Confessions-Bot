import discord
import os

from datetime import datetime
from pytz import timezone
from discord.ext import commands
from dotenv import load_dotenv
from io import BytesIO

from channel_map import retrieve_conf_channel, retrieve_log_channel, add_confessions_channel, add_log_channel

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
	if len(message) != 0 or ctx.message.attatchments != []:

		# parse the message ourselves, since we just want to take in the whole message as is
		message = message.split(' ', 1)
		guild_id = message[0]
		message = message[1]
		print(guild_id, message)

		# verify that this is a valid guild
		try:
			gid = int(guild_id)
		except ValueError:
			await ctx.send('Invalid server id.')

		# verify that there is a channel for this guild
		try:
			channel_id = retrieve_conf_channel(gid)
		except KeyError:
			await ctx.send('This guild is not configured with confessions++ yet.')
		
		# checks to perform: is the bot in the guild and is the user in the guild
		# might be able to eliminate the first check, because of how k v pairs are stored
		guild = bot.get_guild(gid)
		if guild is None:
			await ctx.send('This bot is not in that server.')
		else:
			user_id = ctx.message.author.id
			member = guild.get_member(user_id)
			if member is None:
				await ctx.send('You are not in that server!')

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

		await channel.send(embed=embed)

		# log the confession if the channel set up
		try:
			log_channel_id = retrieve_log_channel(gid)
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

bot.run(BOT_TOKEN)