import os
import redis

import bcrypt
import hashlib

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


def block_user(message_id):
	hashed_user = r.get(name=message_id)
	if hashed_user is None:
		raise KeyError("This message is not in the cache.")
	else:
		r.sadd("blocked", hashed_user)
		r.persist(message_id)


def allow_user(message_id):
	hashed_user = r.get(name=message_id)
	if hashed_user is None:
		raise KeyError("This user has not been blocked.")
	else:
		r.srem("blocked", hashed_user)
		r.expire(message_id, 7200)


# TODO: salt with the server id as well
# cryptographically secure salt? stored w user?
# fear of associating user with salt having to be stored for longer -- would become clear who's blocked
def hash_and_store_user(message_id, user_id, guild_id):
	# salt = bcrypt.gensalt()
	# salted_user = salt + str(user_id)
	hashed = bcrypt.hashpw(bytes(str(guild_id) + str(user_id), encoding='utf-8'), bcrypt.gensalt())
	r.setex(name=message_id, time=21600, value=hashed)

	# store messages for 6 hr at a time so it cycles -- gives mods enough time to act
	# could make this into param for servers to set for less if necessary
	r.expire(message_id, 21600)


def is_blocked(user_id, guild_id):
	user_key = bytes(str(guild_id) + str(user_id), encoding='utf-8')
	return any([bcrypt.checkpw(user_key, user_hash) for user_hash in r.smembers("blocked")])

