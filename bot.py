from __future__ import unicode_literals

import json
import logging
import os

import discord
from discord.ext import commands

# Logging
logging.basicConfig(level=logging.ERROR)


class JetBrains(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        self.jb_guild_id = 433980600391696384
        self.jb_invite = "https://discord.gg/zTUTh2P"

    # Load the latest data into the bot
    def load_data(self):
        with open('data.json') as fl:
            self.data = json.load(fl)

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

    # Find an emoji
    def product_emoji(self, name: str) -> str:
        if name:
            emoji = self.emoji_dict(self.get_guild(self.jb_guild_id))
            if name in emoji:
                return str(emoji[name])
        return ""

    # Main custom group
    def group_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data['emoji_name']) + " **" + data['name'] + "**"]
            if data['description']:
                message.append("*" + data['description'] + "*")
            message.append(("-" * len(message[-1])))
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
                               ("" if ctx.guild and ctx.guild.id == self.jb_guild_id else " - Join with " +
                                                                                          self.jb_invite))
            await ctx.send("\n".join(message))

        return func

    # Custom reddit callback
    def reddit_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data['emoji_name']) + " " + data['name'] + " - Subreddit"]
            if data['subreddit']:
                message.append("**" + self.reddit_url(data['subreddit']) + "**")
            else:
                message.append("*Sorry, there isn't a known subreddit*")
            await ctx.send("\n".join(message))

        return func

    # GitHub custom callback
    def github_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data['emoji_name']) + " " + data['name'] + " - GitHub"]
            if data['github']:
                message.append("**" + self.github_url(data['github']) + "**")
            else:
                message.append("*Sorry, there is no known github link*")
            await ctx.send("\n".join(message))

        return func

    # Custom product page callback
    def page_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data['emoji_name']) + " " + data['name'] + " - Product Page"]
            if data['product_page']:
                message.append("**" + self.product_url(data['product_page']) + "**")
            else:
                message.append("*Sorry, no known product page was found*")
            await ctx.send("\n".join(message))

        return func

    # Issue tracker callback
    def issue_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data['emoji_name']) + " " + data['name'] + " - Issue Tracker"]
            if data['issue_tracker']:
                message.append("**" + self.issue_url(data['issue_tracker']) + "**")
            else:
                message.append("*Sorry, there is no known issue tracker*")
            await ctx.send("\n".join(message))

        return func

    # Channel callback
    def channel_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data['emoji_name']) + " " + data['name'] + " - Discord Channel"]
            channel = self.product_channel(data['channel_name'], data['category_name'])
            if channel:
                message.append("**Please chat about " + data['name'] + " in " + channel.mention + "**" +
                               ("" if ctx.guild and ctx.guild.id == self.jb_guild_id else " - Join with " +
                                                                                          self.jb_invite))
            else:
                message.append("*Sorry, there is no channel*")
            await ctx.send("\n".join(message))

        return func

    # Register all custom commands
    def create_customs(self):
        for item in self.data:
            group = commands.Group(
                name=item['name'].replace(" ", "-").lower().strip(),
                aliases=item['aliases'],
                invoke_without_command=True,
                case_insensitive=True,
                help="Provides information about " + item['name'],
                callback=self.group_callback(item)
            )

            reddit = commands.Command(
                name="reddit",
                aliases=["subreddit", "r", "sub"],
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
                aliases=["url", "product", "site", "website", "jb", "jetbrains", "link"],
                callback=self.page_callback(item)
            )
            group.add_command(page)

            issue = commands.Command(
                name="issue",
                aliases=["issues", "track", "tracker", "youtrack", "yt", "bug", "bugs", "report", "reports"],
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


    @bot.command(aliases=['info', 'about', 'invite', 'add'])
    async def information(ctx: commands.Context):
        """
        Information about JetBot and the JetBrains Community Discord Server
        """
        message = []

        message.append(bot.product_emoji("jetbrainscommunity") + " **JetBrains Server Bot (JetBot)**")
        message.append("*The bot responsible for providing information in, and managing, the JetBrains server.*")
        message.append("View all the commands for JetBrains product and project inforamtion JetBot has in the help "
                       "command `?help`.")
        message.append("\N{LINK SYMBOL} You can use JetBot in your server, invite it with: <https://discordapp.com/"
                       "oauth2/authorize?client_id=" + str(bot.user.id) + "&scope=bot&permissions=8>")

        message.append("")

        message.append(bot.product_emoji("jetbrainscommunity") + " **JetBrains Community Discord Server**")
        message.append("The community home of all the JetBrains products and projects on Discord.")
        message.append("Are you currently a user of JetBrains products or projects?")
        message.append("Would you like to learn more about what JetBrains offers and what licensing options there are?")
        message.append("> Talk to fellow users of the JetBrains software packages and get help with problems you may "
                       "have.")
        message.append("> Chat with other developers, see what they're working on using JetBrains tools and bounce "
                       "ideas around.")
        message.append("\N{BLACK RIGHTWARDS ARROW} **Join the JetBrains Community Discord server: <" + bot.jb_invite +
                       ">**")

        await ctx.send("\n".join(message))


    def license_t_student(title: bool = True) -> list:
        message = []
        if title:
            message.append("`Student Licensing`")
        message.append("As a student in higher education you can request a free student license to use all JetBrains "
                       "products.")
        message.append("\N{LINK SYMBOL} Information: <https://www.jetbrains.com/student/>")
        message.append("\N{CLIPBOARD} Request Form: <https://www.jetbrains.com/shop/eform/students>")
        return message


    def license_t_opensource(title: bool = True) -> list:
        message = []
        if title:
            message.append("`Open Source Licensing`")
        message.append("Do you actively maintain an open source project? If so, you may be able to get a free license "
                       "to all JetBrains products.")
        message.append("\N{LINK SYMBOL} Information: <https://www.jetbrains.com/buy/opensource/>")
        message.append("\N{CLIPBOARD} Request Form: <https://www.jetbrains.com/shop/eform/opensource>")
        return message


    def license_t_personal(title: bool = True) -> list:
        message = []
        if title:
            message.append("`Personal Licenses`")
        message.append("As a normal, personal, user of JetBrains products, you can buy an all products license or a "
                       "specific license for the JetBrains products you use.")
        message.append("\N{LINK SYMBOL} Information: <https://www.jetbrains.com/store/#edition=personal>")
        return message


    def license_t_organization(title: bool = True) -> list:
        message = []
        if title:
            message.append("`Organization Licenses`")
        message.append("If you run an organization, there is different pricing and licensing packages available for "
                       "all JetBrains products individually and as a whole.")
        message.append("\N{LINK SYMBOL} Information: <https://www.jetbrains.com/store/#edition=commercial>")
        return message


    @bot.group(aliases=['licensing', 'buy', 'shop', 'store'],
               invoke_without_command=True, case_insensitive=True)
    async def license(ctx: commands.Context):
        """
        Information about JetBrains product licensing options
        """
        message = []
        message.append(bot.product_emoji("jetbrains") + " **JetBrains Product Licensing Options**")
        message.append("")
        message.extend(license_t_student())
        message.append("")
        message.extend(license_t_opensource())
        message.append("")
        message.extend(license_t_personal())
        message.append("")
        message.extend(license_t_organization())
        await ctx.send("\n".join(message))


    @license.command(name="student", aliases=["school"])
    async def license_student(ctx: commands.Context):
        """
        Information about JetBrains student licensing
        """
        message = []
        message.append(bot.product_emoji("jetbrains") + " **JetBrains Student Licensing**")
        message.extend(license_t_student(False))
        await ctx.send("\n".join(message))


    @bot.command(help=license_student.help, aliases=license_student.aliases)
    async def student(ctx: commands.Context):
        await ctx.invoke(license_student)


    @license.command(name="opensource", aliases=["open", "os"])
    async def license_opensource(ctx: commands.Context):
        """
        Information about JetBrains open source licensing
        """
        message = []
        message.append(bot.product_emoji("jetbrains") + " **JetBrains Open Source Licensing**")
        message.extend(license_t_opensource(False))
        await ctx.send("\n".join(message))


    @bot.command(help=license_opensource.help, aliases=license_opensource.aliases)
    async def opensource(ctx: commands.Context):
        await ctx.invoke(license_opensource)


    @license.command(name="personal", aliases=["normal", "home"])
    async def license_personal(ctx: commands.Context):
        """
        Information about JetBrains personal licensing
        """
        message = []
        message.append(bot.product_emoji("jetbrains") + " **JetBrains Personal Licenses**")
        message.extend(license_t_personal(False))
        await ctx.send("\n".join(message))


    @license.command(name="organization", aliases=["organisation", "business", "work"])
    async def license_organization(ctx: commands.Context):
        """
        Information about JetBrains organization licensing
        """
        message = []
        message.append(bot.product_emoji("jetbrains") + " **JetBrains Organization Licenses**")
        message.extend(license_t_organization(False))
        await ctx.send("\n".join(message))


    @bot.command()
    @commands.check(bot.admin_check)
    async def emoji(ctx: commands.Context):
        """
        Admin command: Update emoji on the JetBrains server
        """
        guild = bot.get_guild(bot.jb_guild_id)
        if guild:
            new = []
            for item in bot.data:
                if item['icon_path'] and item['emoji_name']:
                    if not bot.product_emoji(item['emoji_name']):
                        if os.path.isfile("icons/" + item['icon_path']):
                            with open("icons/" + item['icon_path'], "rb") as f:
                                await guild.create_custom_emoji(name=item['emoji_name'], image=f.read())
                            new.append(item['emoji_name'])
        await ctx.send("Done\n" + "\n".join([bot.product_emoji(f) for f in new]))


    # Start the bot with token from token.txt
    with open("token.txt", "r") as f:
        token = [str(f).strip("\n\r") for f in f.readlines()]
    bot.run(token[0])

else:
    print('Run this by itself')
