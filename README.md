# confessions-bot-plus
A Discord bot with anonymous messages, easy setup in any server and stronger, free moderation features.

## Features

* private message a bot with the `!conf <server id>` command to send your message to a supported server
* user verification (outside members who DM the bot will fail)
* support for images 
* easy setup: use `!set` in the channel you want to make it the confessions channel
* moderation tools: use `!log` in a channel to log confessions with user information

## Running
confessions-bot-plus currently runs on Heroku, with a Redis database to store channels.

To run the bot yourself, locally, install the requirements with
```bash
$ pip3 install -r requirements.txt
```
Then, make sure the REDIS_URL and BOT_TOKEN environment variables are set, and run
```bash
$ python3 bot.py
```

## Planned features
- [x] blacklist user feature
- [ ] video support
- [x] store logs on the backend
- [ ] remove in-server logs for true anonymity (logs supported on feature branch)

