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

    # Register all custom commands
    def create_customs(self):
        for item in self.data.values():
            def group_callback(data):
                async def func(ctx: commands.Context):
                    emoji = self.emoji_dict(self.get_guild(433980600391696384))
                    emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
                    message = [str(emoji) + " **" + data['role_name'] + "**"]
                    if data['subreddit']:
                        message.append("\N{OPEN BOOK} Subreddit: " + self.reddit_url(data['subreddit']))
                    if data['github']:
                        message.append("\N{PACKAGE} GitHub: " + self.github_url(data['github']))
                    if data['product_page']:
                        message.append("\N{LINK SYMBOL} Product Page: " + self.product_url(data['product_page']))
                    if data['issue_tracker']:
                        message.append("\N{LEFT-POINTING MAGNIFYING GLASS} Issue Tracker: " + self.issue_url(
                            data['issue_tracker']))
                    await ctx.send("\n".join(message))

                return func

            group = commands.Group(
                name=item['channel_name'],
                aliases=item['aliases'],
                invoke_without_command=True,
                case_insensitive=True,
                callback=group_callback(item)
            )

            def reddit_callback(data):
                async def func(ctx: commands.Context):
                    emoji = self.emoji_dict(self.get_guild(433980600391696384))
                    emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
                    message = [str(emoji) + " " + data['role_name'] + " - Subreddit"]
                    if data['subreddit']:
                        message.append("**" + self.reddit_url(data['subreddit']) + "**")
                    else:
                        message.append("*No known subreddit*")
                    await ctx.send("\n".join(message))

                return func

            reddit = commands.Command(
                name="reddit",
                aliases=["subreddit", "r"],
                callback=reddit_callback(item)
            )
            group.add_command(reddit)

            def github_callback(data):
                async def func(ctx: commands.Context):
                    emoji = self.emoji_dict(self.get_guild(433980600391696384))
                    emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
                    message = [str(emoji) + " " + data['role_name'] + " - GitHub"]
                    if data['github']:
                        message.append("**" + self.github_url(data['github']) + "**")
                    else:
                        message.append("*No known github*")
                    await ctx.send("\n".join(message))

                return func

            github = commands.Command(
                name="github",
                aliases=["git", "gh"],
                callback=github_callback(item)
            )
            group.add_command(github)

            def page_callback(data):
                async def func(ctx: commands.Context):
                    emoji = self.emoji_dict(self.get_guild(433980600391696384))
                    emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
                    message = [str(emoji) + " " + data['role_name'] + " - Product Page"]
                    if data['product_page']:
                        message.append("**" + self.github_url(data['product_page']) + "**")
                    else:
                        message.append("*No known product page*")
                    await ctx.send("\n".join(message))

                return func

            page = commands.Command(
                name="page",
                aliases=["url", "product", "site", "website", "jb", "jetbrains"],
                callback=page_callback(item)
            )
            group.add_command(page)

            def issue_callback(data):
                async def func(ctx: commands.Context):
                    emoji = self.emoji_dict(self.get_guild(433980600391696384))
                    emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
                    message = [str(emoji) + " " + data['role_name'] + " - Issue Tracker"]
                    if data['issue_tracker']:
                        message.append("**" + self.issue_url(data['issue_tracker']) + "**")
                    else:
                        message.append("*No known issue tracker*")
                    await ctx.send("\n".join(message))

                return func

            issue = commands.Command(
                name="issue",
                aliases=["issues", "track", "tracker", "youtrack", "yt"],
                callback=issue_callback(item)
            )
            group.add_command(issue)

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
