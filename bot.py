from __future__ import unicode_literals

import asyncio
import datetime
import json
import logging
import os
import re
import sys
import time
import traceback
from typing import Dict, Optional

from nextcord import Color, Activity, ActivityType, Status, Guild, CategoryChannel, TextChannel, Role, Message, \
    Member, Permissions
from nextcord.ext import commands

# Logging
logging.basicConfig(level=logging.ERROR)


class JetBrains(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        self.dev_mode = kwargs.get("dev_mode", False)
        self.jb_guild_id = 649591705838026794 if self.dev_mode else 433980600391696384
        self.jb_invite = "https://discord.gg/zTUTh2P"
        self.loop.create_task(self.status_loop())

    async def status_loop(self):
        await self.wait_until_ready()
        while not self.is_closed():
            guild = self.get_guild(self.jb_guild_id)
            playing = "JetBrains users"
            users = ""
            if guild:
                users = "{:,} ".format(guild.member_count)
            try:
                await self.change_presence(
                    activity=Activity(type=ActivityType.watching, name=users + playing),
                    status=Status.online)
            except:
                pass

            await asyncio.sleep(5 * 60)

    # Load the latest data into the bot
    def load_data(self):
        with open("data.json") as fl:
            self.data = json.load(fl)

    # Emoji in a dictionary
    def emoji_dict(self, guild: Guild) -> dict:
        data = {}
        if not guild:
            return data
        for emoji in guild.emojis:
            if emoji.name not in data:
                data[emoji.name] = emoji
        return data

    # Categories in a dictionary
    def category_dict(self, guild: Guild) -> Dict[str, CategoryChannel]:
        data = {}
        if not guild:
            return data
        for category in guild.categories:
            if category.name not in data:
                data[category.name.lower().strip()] = category
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
    def product_channel(self, name: str, category: str) -> Optional[TextChannel]:
        if name and category:
            guild = self.get_guild(self.jb_guild_id)
            categories = self.category_dict(guild)
            if category.lower() in categories:
                channels = [f for f in guild.text_channels if
                            f.name == name and f.category == categories[category.lower().strip()]]
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

    # Find a category
    def product_category(self, name: str) -> Optional[CategoryChannel]:
        if name:
            guild = self.get_guild(self.jb_guild_id)
            category = [f for f in guild.categories if f.name.lower().strip() == name.lower().strip()]
            if category:
                return category[0]
        return None

    # Main custom group
    def group_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data["emoji_name"]) + " **" + data["name"] + "**"]
            if data["description"]:
                message.append("*" + data["description"] + "*")
            message.append(("-" * len(message[-1])))
            if data["subreddit"]:
                message.append("\N{OPEN BOOK} Subreddit: " + self.reddit_url(data["subreddit"]))
            if data["github"]:
                message.append("\N{PACKAGE} GitHub: " + self.github_url(data["github"]))
            if data["product_page"]:
                message.append("\N{LINK SYMBOL} Product Page: " + self.product_url(data["product_page"]))
            if data["issue_tracker"]:
                message.append("\N{LEFT-POINTING MAGNIFYING GLASS} Issue Tracker: " + self.issue_url(
                    data["issue_tracker"]))
            channel = self.product_channel(data["channel_name"], data["category_name"])
            if channel:
                message.append("\N{PAGE FACING UP} Discord Channel: " + channel.mention +
                               ("" if ctx.guild and ctx.guild.id == self.jb_guild_id else " - Join with " +
                                                                                          self.jb_invite))
            await ctx.send("\n".join(message))

        return func

    # Custom reddit callback
    def reddit_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data["emoji_name"]) + " " + data["name"] + " - Subreddit"]
            if data["subreddit"]:
                message.append("**" + self.reddit_url(data["subreddit"]) + "**")
            else:
                message.append("*Sorry, there isn't a known subreddit*")
            await ctx.send("\n".join(message))

        return func

    # GitHub custom callback
    def github_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data["emoji_name"]) + " " + data["name"] + " - GitHub"]
            if data["github"]:
                message.append("**" + self.github_url(data["github"]) + "**")
            else:
                message.append("*Sorry, there is no known github link*")
            await ctx.send("\n".join(message))

        return func

    # Custom product page callback
    def page_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data["emoji_name"]) + " " + data["name"] + " - Product Page"]
            if data["product_page"]:
                message.append("**" + self.product_url(data["product_page"]) + "**")
            else:
                message.append("*Sorry, no known product page was found*")
            await ctx.send("\n".join(message))

        return func

    # Issue tracker callback
    def issue_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data["emoji_name"]) + " " + data["name"] + " - Issue Tracker"]
            if data["issue_tracker"]:
                message.append("**" + self.issue_url(data["issue_tracker"]) + "**")
            else:
                message.append("*Sorry, there is no known issue tracker*")
            await ctx.send("\n".join(message))

        return func

    # Channel callback
    def channel_callback(self, data):
        async def func(ctx: commands.Context):
            message = [self.product_emoji(data["emoji_name"]) + " " + data["name"] + " - Discord Channel"]
            channel = self.product_channel(data["channel_name"], data["category_name"])
            if channel:
                message.append("**Please chat about " + data["name"] + " in " + channel.mention + "**" +
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
                self.group_callback(item),
                name=item["name"].replace(" ", "-").lower().strip(),
                aliases=item["aliases"],
                invoke_without_command=True,
                case_insensitive=True,
                help="Info about " + item["name"]
            )

            reddit = commands.Command(
                self.reddit_callback(item),
                name="reddit",
                aliases=["subreddit", "r", "sub"]
            )
            group.add_command(reddit)

            github = commands.Command(
                self.github_callback(item),
                name="github",
                aliases=["git", "gh"]
            )
            group.add_command(github)

            page = commands.Command(
                self.page_callback(item),
                name="page",
                aliases=["url", "product", "site", "website", "jb", "jetbrains", "link"]
            )
            group.add_command(page)

            issue = commands.Command(
                self.issue_callback(item),
                name="issue",
                aliases=["issues", "track", "tracker", "youtrack", "yt", "bug", "bugs", "report", "reports"]
            )
            group.add_command(issue)

            channel = commands.Command(
                self.channel_callback(item),
                name="channel",
                aliases=["chan", "chat", "text", "discord"]
            )
            group.add_command(channel)

            self.add_command(group)

    # Check for admin commands
    async def admin_check(self, ctx: commands.Context) -> bool:
        if ctx.author.id in [541305895544422430]:
            return True
        return False

    # Ignore some errors
    async def on_command_error(self, ctx: commands.Context, error):
        if hasattr(ctx.command, "on_error"):
            return

        ignored = (commands.CommandNotFound, commands.DisabledCommand)
        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        # Unhandled error
        lines = traceback.format_exception(type(error), error, error.__traceback__)
        print("".join(lines))

    # Employee email verification
    async def email_verify(self, message: Message):
        guild = self.get_guild(self.jb_guild_id)
        if guild:
            channel = [f for f in guild.text_channels if f.name.lower().strip() == "employee-verification"]
            if channel:
                channel = channel[0]
                if message.channel.id == channel.id:
                    pattern = re.compile("(?:.*\s+)*(\S+@jetbrains\.com).*", re.DOTALL)
                    match = pattern.match(message.content)
                    if not match:
                        try:
                            await message.author.send("Sorry, I could not find a valid JetBrains.com email in the"
                                                      " message you sent to {}.".format(channel.mention))
                        except:
                            pass
                    else:
                        try:
                            await message.author.send("Thank you, your email ({}) has been passed onto the server"
                                                      " admins for verification!".format(match.group(1)))
                        except:
                            pass
                        role = [f for f in guild.roles if f.name.lower().strip() == "admin"]
                        channel = self.product_channel("admin-chat", "admins")
                        if channel:
                            await channel.send("{0.mention} `{0.name}#{0.discriminator} {0.id}` has requested"
                                               " JetBrains employee verification with the email `{1}` {2}".format(
                                message.author, match.group(1), role[0].mention if role else ""))
                    await message.delete()

    # Handle messages
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        await self.email_verify(message)
        await self.process_commands(message)

    # Acknowledge bot is ready to go
    async def on_ready(self):
        print("Logged in as")
        print(bot.user.name)
        print(bot.user.id)
        print("https://discord.com/oauth2/authorize?client_id=" + str(bot.user.id) + "&scope=bot&permissions=8")
        print("------")
        self.load_data()
        self.create_customs()


if __name__ == "__main__":

    # Dev Mode
    dev_mode = False
    if (len(sys.argv) > 1 and sys.argv[1] and sys.argv[1].strip() == "dev") or dev_mode:
        dev_mode = True

    # Create the bot instance
    bot = JetBrains(command_prefix="?", dev_mode=dev_mode)


    @bot.command(aliases=["info", "about", "invite", "add", "author", "owner", "server", "support",
                          "jetbot", "jetbrains"])
    async def information(ctx: commands.Context):
        """
        JetBot & JetBrains Community Discord Server info
        """
        await ctx.send("\n".join([
            bot.product_emoji("jetbrainscommunity") + " **JetBrains Server Bot (JetBot)**",
            "*The bot responsible for providing information in, and managing, the JetBrains server.*",
            "View all the commands for JetBrains product and project inforamtion JetBot has in the help "
            "command `?help`.",
            "\N{LINK SYMBOL} You can use JetBot in your server, invite it with: <https://discord.com/"
            "oauth2/authorize?client_id=" + str(bot.user.id) + "&scope=bot&permissions=8>.",
            "*JetBot was created and is maintained by v4#1503 but is also open source at <https://github.com/"
            "JetBrains-Community/discord>.*", "",
            bot.product_emoji("jetbrainscommunity") + " **JetBrains Community Discord Server**",
            "The community home of all the JetBrains products and projects on Discord.",
            "Are you currently a user of JetBrains products or projects?",
            "Would you like to learn more about what JetBrains offers and what licensing options there are?",
            "> Talk to fellow users of the JetBrains software packages and get help with problems you may "
            "have.",
            "> Chat with other developers, see what they're working on using JetBrains tools and bounce "
            "ideas around.",
            "\N{BLACK RIGHTWARDS ARROW} **Join the JetBrains Community Discord server: <" + bot.jb_invite +
            ">**", "", bot.product_emoji("jetbrains") + " **JetBrains s.r.o**",
            "JetBrains is a cutting-edge software vendor specializing in the creation of intelligent "
            "development tools, including IntelliJ IDEA – the leading Java IDE, and the Kotlin programming "
            "language.", "\N{LINK SYMBOL} You can find out more on their website: <https://www.jetbrains.com/>"
        ]))


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


    @bot.group(aliases=["licensing", "buy", "shop", "store"],
               invoke_without_command=True, case_insensitive=True)
    async def license(ctx: commands.Context):
        """
        JetBrains product licensing options
        """
        await ctx.send("\n".join([
            bot.product_emoji("jetbrains") + " **JetBrains Product Licensing Options**",
            "", license_t_student(),
            "", license_t_opensource(),
            "", license_t_personal(),
            "", license_t_organization()
        ]))


    @license.command(name="student", aliases=["school"])
    async def license_student(ctx: commands.Context):
        """
        JetBrains student licensing info
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
        JetBrains open source licensing info
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
        JetBrains personal licensing info
        """
        message = []
        message.append(bot.product_emoji("jetbrains") + " **JetBrains Personal Licenses**")
        message.extend(license_t_personal(False))
        await ctx.send("\n".join(message))


    @license.command(name="organization", aliases=["organisation", "business", "work"])
    async def license_organization(ctx: commands.Context):
        """
        JetBrains organization licensing info
        """
        message = []
        message.append(bot.product_emoji("jetbrains") + " **JetBrains Organization Licenses**")
        message.extend(license_t_organization(False))
        await ctx.send("\n".join(message))


    @bot.command()
    async def ping(ctx: commands.Context):
        """
        Ping JetBot to test response time
        """
        latency = (datetime.datetime.utcnow() - ctx.message.created_at).total_seconds() * 1000

        before = time.monotonic()
        msg = await ctx.send("Pinging...")
        after = time.monotonic()

        heartbeat = (after - before) * 1000
        wslatency = bot.latency * 1000

        message = ["**JetBot Ping**"]
        message.append(("-" * len(message[-1])))
        message.append("\N{STOPWATCH} Latency: {:.0f}ms".format(latency))
        message.append("\N{BEATING HEART} Heartbeat: {:.0f}ms".format(heartbeat))
        message.append("\N{ANTENNA WITH BARS} WS Latency: {:.0f}ms".format(wslatency))

        await msg.edit(content="\n".join(message))


    @bot.command()
    @commands.check(bot.admin_check)
    async def emoji(ctx: commands.Context):
        """
        Admin: Update emoji on the JetBrains server
        """
        guild = bot.get_guild(bot.jb_guild_id)
        if guild:
            new = []
            for item in bot.data:
                if item["icon_path"] and item["emoji_name"]:
                    if not bot.product_emoji(item["emoji_name"]):
                        if os.path.isfile("icons/" + item["icon_path"]):
                            with open("icons/" + item["icon_path"], "rb") as f:
                                print("Creating icon... " + item["icon_path"])
                                await guild.create_custom_emoji(name=item["emoji_name"], image=f.read())
                            new.append(item["emoji_name"])
                    else:
                        print(item["icon_path"] + " icon already exists")

        # Done
        await ctx.send("Done\n" + "\n".join([bot.product_emoji(f) for f in new]))


    @bot.command()
    @commands.check(bot.admin_check)
    async def channels(ctx: commands.Context):
        """
        Admin: Update channels on the JetBrains server
        """
        new = []
        guild = bot.get_guild(bot.jb_guild_id)
        if guild:
            categories = {}
            mods = [f for f in ctx.guild.roles if f.name.lower().strip() == "-"][0]
            default_title = "Discuss anything about {} here."
            title_map = {
                "open source": "Chat about the open source project {} here.",
                "educational": "Chat about the educational tool {} here."
            }
            # Create product channels
            for item in bot.data:
                if item["channel_name"] and item["category_name"]:
                    # Get the category
                    if item["category_name"].lower().strip() in categories:
                        category = categories[item["category_name"].lower().strip()]
                    else:
                        category = bot.product_category(item["category_name"])
                        if not category:
                            print("Creating category... " + item["category_name"])
                            category = await guild.create_category(item["category_name"])
                        categories[item["category_name"].lower().strip()] = category

                    # Get the channel
                    channel = bot.product_channel(item["channel_name"], item["category_name"])
                    if not channel:
                        print("Creating channel... " + item["channel_name"])
                        channel = await guild.create_text_channel(item["channel_name"], category=category)
                        new.append(channel)

                    # Set permissions
                    print("Updating channel... " + item["channel_name"] + " in " + item["category_name"])
                    for overwrite in channel.overwrites:
                        await channel.set_permissions(overwrite, overwrite=None)
                    await channel.edit(slowmode_delay=5, sync_permissions=True)

                    # Handle read-only
                    if "read_only" in item and item["read_only"]:
                        # Send the read-only message
                        last = await channel.history(limit=1).flatten()
                        if not last or last[0].content != item["read_only"]:
                            await channel.send(item["read_only"])

                        # Set the topic
                        product_emoji = bot.product_emoji(item["emoji_name"])
                        title = "{0} {1} {0}".format(product_emoji, item["name"]) if product_emoji else item["name"]
                        if channel.topic != title:
                            await channel.edit(topic=title)

                        # Set permissions
                        await channel.set_permissions(guild.default_role,
                                                      send_messages=False,
                                                      send_messages_in_threads=False,
                                                      create_private_threads=False,
                                                      create_public_threads=False)
                    else:
                        # Set the topic
                        product_category = category.name.lower().strip()
                        product_emoji = bot.product_emoji(item["emoji_name"])
                        title = title_map[product_category] if product_category in title_map else default_title
                        title = title.format(item["name"])
                        title = "{0} {1} {0}".format(product_emoji, title) if product_emoji else title
                        if channel.topic != title:
                            await channel.edit(topic=title)

            # Set category perms
            for category in categories.values():
                print("Updating category... " + category.name)
                for overwrite in category.overwrites:
                    await category.set_permissions(overwrite, overwrite=None)

        # Done
        await ctx.send("Done\n" + "\n".join([f.mention for f in new]))


    # Start the bot with token from token.txt
    with open("token" + ("_dev" if dev_mode else "") + ".txt", "r") as f:
        token = [str(f).strip("\n\r") for f in f.readlines()]
    bot.run(token[0], reconnect=False)

else:
    print("Run this by itself")
