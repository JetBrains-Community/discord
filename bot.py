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
    def text_subreddit(self, data: str) -> str:
        return "\N{OPEN BOOK} Subreddit: <https://reddit.com/r/" + data + ">"

    # Custom text for github
    def text_github(self, data: str) -> str:
        return "\N{PACKAGE} GitHub: <https://github.com/JetBrains/" + data + ">"

    # Custom text for product
    def text_product(self, data: str) -> str:
        return "\N{LINK SYMBOL} Product Page: <" + data + ">"

    # Custom text for issues
    def text_issues(self, data: str) -> str:
        return "\N{LEFT-POINTING MAGNIFYING GLASS} Issue Tracker: <https://youtrack.jetbrains.com/issues/" + data + ">"

    # Register all custom commands
    def create_customs(self):
        for item in self.data.values():
            def group_callback(data):
                async def func(ctx: commands.Context):
                    emoji = self.emoji_dict(self.get_guild(433980600391696384))
                    emoji = emoji[data['emoji_name']] if data['emoji_name'] in emoji else ""
                    message = []
                    message.append(str(emoji) + " **" + data['role_name'] + "**")
                    if data['subreddit']:
                        message.append(self.text_subreddit(data['subreddit']))
                    if data['github']:
                        message.append(self.text_github(data['github']))
                    if data['product_page']:
                        message.append(self.text_product(data['product_page']))
                    if data['issue_tracker']:
                        message.append(self.text_issues(data['issue_tracker']))
                    message = "\n".join(message)
                    await ctx.send(message)

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
                    # TODO: this (emoji product - type \n **<link>**) [must handle none]
                    pass

                return func

            reddit = commands.Command(
                name="reddit",
                aliases=["subreddit", "r"],
                callback=reddit_callback
            )
            group.add_command(reddit)

            def github_callback(data):
                async def func(ctx: commands.Context):
                    # TODO: this (emoji product - type \n **<link>**) [must handle none]
                    pass

                return func

            github = commands.Command(
                name="github",
                aliases=["git", "gh"],
                callback=github_callback
            )
            group.add_command(github)

            def page_callback(data):
                async def func(ctx: commands.Context):
                    # TODO: this (emoji product - type \n **<link>**) [must handle none]
                    pass

                return func

            page = commands.Command(
                name="page",
                aliases=["url", "product", "site", "website", "jb", "jetbrains"],
                callback=page_callback
            )
            group.add_command(page)

            def issue_callback(data):
                async def func(ctx: commands.Context):
                    # TODO: this (emoji product - type \n **<link>**) [must handle none]
                    pass

                return func

            issue = commands.Command(
                name="issue",
                aliases=["issues", "track", "tracker", "youtrack", "yt"],
                callback=issue_callback
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
