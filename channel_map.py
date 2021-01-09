import os
import redis

from dotenv import load_dotenv

load_dotenv()

r = redis.from_url(os.getenv('REDIS_URL'))
channel_map = {int(k): int(v) for k, v in r.hgetall("conf").items()}
logging_map = {int(k): int(v) for k, v in r.hgetall("log").items()}

def retrieve_conf_channel(guild_id):
	try:
		channel_id = channel_map[guild_id]
	except KeyError:
		raise KeyError("No such channel id exists")
	else:
		return int(channel_id)


def retrieve_log_channel(guild_id):
	try:
		channel_id = logging_map[guild_id]
	except KeyError:
		raise KeyError("No such channel id exists")
	else:
		return int(channel_id)


def add_confessions_channel(guild_id, channel_id):
	channel_map[guild_id] = channel_id
	r.hset("conf", key=guild_id, value=channel_id)


def add_log_channel(guild_id, channel_id):
	logging_map[guild_id] = channel_id
	r.hset("log", key=guild_id, value=channel_id)