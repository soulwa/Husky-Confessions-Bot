channel_map = dict()
logging_map = dict()

def retrieve_conf_channel(guild_id):
	try:
		channel_id = channel_map[guild_id]
	except KeyError:
		raise KeyError("No such channel id exists")
	else:
		return channel_id


def retrieve_log_channel(guild_id):
	try:
		channel_id = channel_map[guild_id]
	except KeyError:
		raise KeyError("No such channel id exists")
	else:
		return channel_id


def add_confessions_channel(guild_id, channel_id):
	channel_map[guild_id] = channel_id


def add_log_channel(guild_id, channel_id):
	logging_map[guild_id] = channel_id