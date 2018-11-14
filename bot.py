from __future__ import unicode_literals

import json
import logging

import discord
from discord.ext import commands

# Logging
logging.basicConfig(level=logging.ERROR)


class JetBrains(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = {}
        self.jb_guild_id = 433980600391696384
        self.jb_invite = "https://discord.gg/zTUTh2P"

    # Load the latest data into the bot
    def load_data(self):
        with open('data.json') as fl:
            self.data = {f['channel_name']: f for f in json.load(fl)}

    # Emoji in a dictionary
    def emoji_dict(self, guild: discord.Guild) -> dict:
        data = {}
        if not guild:
            return data
        for emoji in guild.emojis:
            if emoji.name not in data:
                data[emoji.name] = emoji
        return data

    # Categories in a dictionary
    def category_dict(self, guild: discord.Guild) -> dict:
        data = {}
        if not guild:
            return data
        for category in guild.categories:
            if category.name not in data:
                data[category.name] = category
        return data

    # Channels in a dictionary
    def channels_dict(self, channels: list) -> dict:
        data = {}
        if not channels:
            return data
        for channel in channels:
            if channel.name not in data:
                data[channel.name] = channel
        return data

    # Custom text for subreddit
    def reddit_url(self, data: str) -> str:
        return "<https://reddit.com/r/" + data + ">"

    # Custom text for github
    def github_url(self, data: str) -> str:
        return "<https://github.com/JetBrains/" + data + ">"

    # Custom text for product
    def product_url(self, data: str) -> str:
        return "<" + data + ">"

    # Custom text for issues
    def issue_url(self, data: str) -> str:
        return "<https://youtrack.jetbrains.com/issues/" + data + ">"

    # Find a product channel
    def product_channel(self, name: str, category: str) -> discord.TextChannel:
        if name and category:
            guild = self.get_guild(self.jb_guild_id)
            categories = self.category_dict(guild)
            if category in categories:
                channels = [f for f in guild.text_channels if f.name == name and f.category == categories[category]]
                if channels:
                    return channels[0]
        return None

    # Main custom group
    def group_callback(self, data):
        async def func(ctx: commands.Context):
            guild = self.get_guild(self.jb_guild_id)
            emoji = self.emoji_dict(guild)
            emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
            message = [str(emoji) + " **" + data['name'] + "**"]
            if data['description']:
                message.append("*" + data['description'] + "*")
            if data['subreddit']:
                message.append("\N{OPEN BOOK} Subreddit: " + self.reddit_url(data['subreddit']))
            if data['github']:
                message.append("\N{PACKAGE} GitHub: " + self.github_url(data['github']))
            if data['product_page']:
                message.append("\N{LINK SYMBOL} Product Page: " + self.product_url(data['product_page']))
            if data['issue_tracker']:
                message.append("\N{LEFT-POINTING MAGNIFYING GLASS} Issue Tracker: " + self.issue_url(
                    data['issue_tracker']))
            channel = self.product_channel(data['channel_name'], data['category_name'])
            if channel:
                message.append("\N{PAGE FACING UP} Discord Channel: " + channel.mention +
                               (" - Join with " + self.jb_invite if ctx.guild.id != self.jb_guild_id else ""))
            await ctx.send("\n".join(message))

        return func

    # Custom reddit callback
    def reddit_callback(self, data):
        async def func(ctx: commands.Context):
            emoji = self.emoji_dict(self.get_guild(self.jb_guild_id))
            emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
            message = [str(emoji) + " " + data['name'] + " - Subreddit"]
            if data['subreddit']:
                message.append("**" + self.reddit_url(data['subreddit']) + "**")
            else:
                message.append("*Sorry, there isn't a known subreddit*")
            await ctx.send("\n".join(message))

        return func

    # GitHub custom callback
    def github_callback(self, data):
        async def func(ctx: commands.Context):
            emoji = self.emoji_dict(self.get_guild(self.jb_guild_id))
            emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
            message = [str(emoji) + " " + data['name'] + " - GitHub"]
            if data['github']:
                message.append("**" + self.github_url(data['github']) + "**")
            else:
                message.append("*Sorry, there is no known github link*")
            await ctx.send("\n".join(message))

        return func

    # Custom product page callback
    def page_callback(self, data):
        async def func(ctx: commands.Context):
            emoji = self.emoji_dict(self.get_guild(self.jb_guild_id))
            emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
            message = [str(emoji) + " " + data['name'] + " - Product Page"]
            if data['product_page']:
                message.append("**" + self.product_url(data['product_page']) + "**")
            else:
                message.append("*Sorry, no known product page was found*")
            await ctx.send("\n".join(message))

        return func

    # Issue tracker callback
    def issue_callback(self, data):
        async def func(ctx: commands.Context):
            emoji = self.emoji_dict(self.get_guild(self.jb_guild_id))
            emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
            message = [str(emoji) + " " + data['name'] + " - Issue Tracker"]
            if data['issue_tracker']:
                message.append("**" + self.issue_url(data['issue_tracker']) + "**")
            else:
                message.append("*Sorry, there is no known issue tracker*")
            await ctx.send("\n".join(message))

        return func

    # Channel callback
    def channel_callback(self, data):
        async def func(ctx: commands.Context):
            guild = self.get_guild(self.jb_guild_id)
            emoji = self.emoji_dict(guild)
            emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
            message = [str(emoji) + " " + data['name'] + " - Discord Channel"]
            channel = self.product_channel(data['channel_name'], data['category_name'])
            if channel:
                message.append("**Please chat about " + data['name'] + " in " + channel.mention + "**" +
                               (" - Join with " + self.jb_invite if ctx.guild.id != self.jb_guild_id else ""))
            else:
                message.append("*Sorry, there is no channel*")
            await ctx.send("\n".join(message))

        return func

    # Register all custom commands
    def create_customs(self):
        for item in self.data.values():
            group = commands.Group(
                name=item['name'].replace(" ", "-").lower().strip(),
                aliases=item['aliases'],
                invoke_without_command=True,
                case_insensitive=True,
                callback=self.group_callback(item)
            )

            reddit = commands.Command(
                name="reddit",
                aliases=["subreddit", "r"],
                callback=self.reddit_callback(item)
            )
            group.add_command(reddit)

            github = commands.Command(
                name="github",
                aliases=["git", "gh"],
                callback=self.github_callback(item)
            )
            group.add_command(github)

            page = commands.Command(
                name="page",
                aliases=["url", "product", "site", "website", "jb", "jetbrains"],
                callback=self.page_callback(item)
            )
            group.add_command(page)

            issue = commands.Command(
                name="issue",
                aliases=["issues", "track", "tracker", "youtrack", "yt"],
                callback=self.issue_callback(item)
            )
            group.add_command(issue)

            channel = commands.Command(
                name="channel",
                aliases=["chan", "chat", "text", "discord"],
                callback=self.channel_callback(item)
            )
            group.add_command(channel)

            self.add_command(group)

    # Check for admin commands
    async def admin_check(self, ctx: commands.Context) -> bool:
        if ctx.author.id in [193060889111298048]:
            return True
        return False

    # Acknowledge bot is ready to go
    async def on_ready(self):
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print("https://discordapp.com/oauth2/authorize?client_id=" + str(bot.user.id) + "&scope=bot&permissions=8")
        print('------')
        self.load_data()
        self.create_customs()


if __name__ == '__main__':

    # Create the bot instance
    bot = JetBrains(command_prefix="?")
    # bot.remove_command('help')

    # Start the bot with token from token.txt
    with open("token.txt", "r") as f:
        token = [str(f).strip("\n\r") for f in f.readlines()]
    bot.run(token[0])

else:
    print('Run this by itself')
