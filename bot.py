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

import aiomysql
import discord
from discord.ext import commands

# Logging
logging.basicConfig(level=logging.ERROR)


class JetBrains(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        self.dev_mode = kwargs.get("dev_mode", False)
        self.role_color = discord.Colour(0x18d68c)  # Normal
        # self.role_color = discord.Colour(0xFB5502)  # Halloween
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
                    activity=discord.Activity(type=discord.ActivityType.watching, name=users + playing),
                    status=discord.Status.online)
            except:
                pass

            await asyncio.sleep(5 * 60)

    # Load the latest data into the bot
    def load_data(self):
        with open("data.json") as fl:
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
    def category_dict(self, guild: discord.Guild) -> Dict[str, discord.CategoryChannel]:
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
    def product_channel(self, name: str, category: str) -> Optional[discord.TextChannel]:
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

    # Find a product role
    def product_role(self, name: str) -> Optional[discord.Role]:
        if name:
            guild = self.get_guild(self.jb_guild_id)
            role = [f for f in guild.roles if f.name == name]
            if role:
                return role[0]
        return None

    # Find a category
    def product_category(self, name: str) -> Optional[discord.CategoryChannel]:
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
                message.append("*Sorry, there isn\"t a known subreddit*")
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

    # Staff email verification
    async def email_verify(self, message: discord.message):
        guild = self.get_guild(self.jb_guild_id)
        if guild:
            channel = [f for f in guild.text_channels if f.name.lower().strip() == "staff-verify"]
            if channel:
                channel = channel[0]
                if message.channel.id == channel.id:
                    pattern = re.compile("(?:.*\s+)*(\S+@jetbrains\.com).*", re.DOTALL)
                    match = pattern.match(message.content)
                    if not match:
                        try:
                            await message.author.send("Sorry, I could not find a valid JetBrains email in the message"
                                                      " you sent to {}.".format(channel.mention))
                        except:
                            pass
                    else:
                        try:
                            await message.author.send("Thank you, your email ({}) has been passed onto the server"
                                                      " admins for verification!".format(match.group(1)))
                        except:
                            pass
                        role = [f for f in guild.roles if f.name.lower().strip() == "admin"]
                        channel = self.product_channel("chat", "admins")
                        if channel:
                            await channel.send("{0.mention} `{0.name}#{0.discriminator} {0.id}` has requested"
                                               " JetBrains staff verification with the email `{1}` {2}".format(
                                message.author, match.group(1), role[0].mention if role else ""))
                    await message.delete()

    # Handle messages
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        await self.email_verify(message)
        await self.process_commands(message)

    # Acknowledge bot is ready to go
    async def on_ready(self):
        print("Logged in as")
        print(bot.user.name)
        print(bot.user.id)
        print("https://discordapp.com/oauth2/authorize?client_id=" + str(bot.user.id) + "&scope=bot&permissions=8")
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
            "\N{LINK SYMBOL} You can use JetBot in your server, invite it with: <https://discordapp.com/"
            "oauth2/authorize?client_id=" + str(bot.user.id) + "&scope=bot&permissions=8>.",
            "*JetBot was created and is maintained by v4#1503 and is also open source at <https://github.com/"
            "JetBrains-Community/discord>.*", "",
            bot.product_emoji("jetbrainscommunity") + " **JetBrains Community Discord Server**",
            "The community home of all the JetBrains products and projects on Discord.",
            "Are you currently a user of JetBrains products or projects?",
            "Would you like to learn more about what JetBrains offers and what licensing options there are?",
            "> Talk to fellow users of the JetBrains software packages and get help with problems you may "
            "have.",
            "> Chat with other developers, see what they\"re working on using JetBrains tools and bounce "
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
    async def users(ctx: commands.Context, target: discord.Member = None):
        """
        Find JetBrains IDE users mutual with the bot and target
        """
        if not target: target = ctx.author
        test_strings = [f["name"].lower() for f in bot.data if len(f["name"].lower()) > 3]  # "hub" matches badly
        test_strings.append("jetbrains")

        found = []
        for member in bot.get_all_members():
            if member not in [f[0] for f in found]:
                if member.status is not discord.Status.offline and member.activity:
                    matches = [f for f in test_strings if f in member.activity.name.lower()]
                    if matches:
                        if member.guild.get_member(target.id) and member not in bot.get_guild(
                                433980600391696384).members:
                            found.append([member, matches[0]])  # save the user and the match

        header = "**JetBrains IDE Users not in the JetBrains Community Discord Server**" \
                 "\n*Users that are in mutual servers with you and JetBot*" \
                 "\nWhy not ask them if they\"d like to join our community?" \
                 " They can use the invite <" + bot.jb_invite + ">."

        found = ["\n{0.mention} `{0.name}#{0.discriminator}` `{0.id}` Playing: `{1}` Match: `{2}`".format(
            f[0], f[0].activity.name, f[1]) for f in found] or ["\n`No users were found :(`"]

        msg = ""
        msg += header
        for item in found:
            if len(msg + item) > 2000:
                await ctx.send(msg)
                msg = ""
            msg += item
        if msg:
            await ctx.send(msg)


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
    async def roles(ctx: commands.Context):
        """
        Admin: Update roles on the JetBrains server
        """
        guild = bot.get_guild(bot.jb_guild_id)
        if guild:
            new = []
            positions = []

            # Create product roles
            for item in bot.data:
                if item["role_name"]:
                    role = bot.product_role(item["role_name"])
                    if not role:
                        print("Creating role... " + item["role_name"])
                        role = await guild.create_role(
                            name=item["role_name"],
                            permissions=discord.Permissions.none(),
                            color=bot.role_color,
                            hoist=False,
                            mentionable=False
                        )
                        new.append(role)
                    else:
                        print(item["role_name"] + " role already exists")
                        if role.color != bot.role_color:
                            await role.edit(color=bot.role_color)
                    positions.append(role.position)

            # Create hide role
            role = bot.product_role("Hide Unsubscribed Channels")
            if not role:
                print("Creating role... Hide Unsubscribed Channels")
                role = await guild.create_role(
                    name="Hide Unsubscribed Channels",
                    permissions=discord.Permissions.none(),
                    color=discord.Colour(0x7D7D7D),
                    hoist=False,
                    mentionable=False
                )
                new.append(role)
            else:
                print("Hide Unsubscribed Channels role already exists")
            positions = min(positions)
            if role.position != positions:
                await role.edit(position=positions)

        # Done
        await ctx.send("Done\n" + "\n".join([f.mention for f in new]))


    @bot.command()
    @commands.check(bot.admin_check)
    async def channels(ctx: commands.Context):
        """
        Admin: Update channels on the JetBrains server
        """
        guild = bot.get_guild(bot.jb_guild_id)
        if guild:
            categories = {}
            new = []
            hide = [f for f in guild.roles if f.name.strip() == "Hide Unsubscribed Channels"][0]
            mods = [f for f in ctx.guild.roles if f.name.lower().strip() == "-"][0]
            default_title = "Discuss anything about {} here."
            title_map = {
                "open source": "Chat about the open source project {} here.",
                "educational": "Chat about the educational tool {} here."
            }
            # Create product channels
            for item in bot.data:
                if item["emoji_name"] and item["role_name"] and item["channel_name"] and item["category_name"]:
                    # Get the role and emoji
                    role = bot.product_role(item["role_name"])
                    emoji = bot.product_emoji(item["emoji_name"])
                    if role and emoji:
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
                        await channel.set_permissions(guild.default_role, send_messages=False)
                        await channel.set_permissions(role, send_messages=True, read_messages=True)
                        await channel.set_permissions(hide, read_messages=False)
                        await channel.set_permissions(mods, send_messages=True, read_messages=True)

                        # Set topic
                        title = default_title
                        if category.name.lower().strip() in title_map:
                            title = title_map[category.name.lower().strip()]
                        title = "{0} \N{PUBLIC ADDRESS LOUDSPEAKER} Unlock this channel using #unlock-channels - " \
                                "{1} {0}".format(emoji, title.format(item["name"]))
                        if channel.topic != title:
                            await channel.edit(topic=title)

            # Set category perms
            for item in categories.values():
                print("Updating category... " + item.name)
                await item.set_permissions(guild.default_role, send_messages=False)
                await item.set_permissions(mods, send_messages=True)

        # Done
        await ctx.send("Done\n" + "\n".join([f.mention for f in new]))


    @bot.command()
    @commands.check(bot.admin_check)
    async def reactions(ctx: commands.Context):
        """
        Admin: Update reaction roles on the JetBrains server
        """
        guild = bot.get_guild(bot.jb_guild_id)
        if guild:
            # Get the categories
            info_category = bot.product_category("Information")
            if not info_category:
                print("Creating category... Information")
                info_category = await guild.create_category("Information")
            general_category = bot.product_category("General")
            if not general_category:
                print("Creating category... General")
                general_category = await guild.create_category("General")

            # Get the channels
            unlock = bot.product_channel("unlock-channels", "Information")
            if not unlock:
                print("Creating channel... unlock-channels")
                unlock = await guild.create_text_channel("unlock-channels", category=info_category)
            await unlock.set_permissions(ctx.guild.default_role, send_messages=False)
            offtopic = bot.product_channel("off-topic", "General")
            if not offtopic:
                print("Creating channel... off-topic")
                offtopic = await guild.create_text_channel("off-topic", category=general_category)

            # Create db connection for Restarter"s react roles from db.txt
            with open("db.txt", "r") as f:
                db = [str(f).strip("\n\r") for f in f.readlines()]
            conn = await aiomysql.connect(host=db[0], port=3306, user=db[1], password=db[2], db=db[3], loop=bot.loop)
            cursor = await conn.cursor()

            # Remove old content
            async for message in unlock.history(limit=None):
                await message.delete()
            await cursor.execute("DELETE FROM restarter_reactroles WHERE guild = %s", (guild.id))
            await cursor.execute("DELETE FROM restarter_roles WHERE guild = %s", (guild.id))
            await conn.commit()

            # Hide channels message
            print("Creating react role... hide")
            hide = await unlock.send("**React to the following messages with JetBrains product and project emoji to"
                                     " unlock the relevant discussion channels in this server.**"
                                     "\n\nClick on one of the reactions already on the messages to unlock the role."
                                     " Remove your reaction to remove your role."
                                     "\n\nReactions not working for you? Head over to {0} and type `r.roles` to use"
                                     " commands instead."
                                     "\n\nWant to hide the channels you aren\"t active in? React to this message with"
                                     " \N{NO ENTRY SIGN} to hide any product channel you aren\"t \"subscribed\" to"
                                     " using the roles below. Remove your reaction to show all JetBrains product"
                                     " channels again. Can\"t use reactions, head to {0} and use \"r.hide\" to toggle"
                                     " the role.".format(offtopic.mention))
            await hide.add_reaction("\N{NO ENTRY SIGN}")
            hide_role = bot.product_role("Hide Unsubscribed Channels")
            await cursor.execute("INSERT INTO restarter_reactroles (message,emoji,role,guild) VALUES (%s,%s,%s,%s)",
                                 (hide.id, "\N{NO ENTRY SIGN}".encode("ascii", "namereplace").decode(), hide_role.id,
                                  guild.id))
            await cursor.execute("INSERT INTO restarter_roles (guild,role,alias) VALUES (%s,%s,%s)",
                                 (guild.id, hide_role.id, "hide"))
            await conn.commit()

            # Generate new messages
            message = None
            content = []
            counter = 0
            for item in bot.data:
                if item["emoji_name"] and item["role_name"] and item["channel_name"] and item["category_name"]:
                    role = bot.product_role(item["role_name"])
                    emoji = bot.product_emoji(item["emoji_name"])
                    channel = bot.product_channel(item["channel_name"], item["category_name"])
                    if role and emoji and channel:
                        # Send message
                        if counter % 5 == 0:
                            if message:
                                await message.edit(content="\n".join(content))
                                content = []
                            message = await unlock.send("Generating react roles...")

                        # Add next product
                        print("Creating react role... " + channel.name)
                        content.append("{} - {}".format(emoji, channel.mention))
                        await message.add_reaction(emoji)
                        await cursor.execute("INSERT INTO restarter_reactroles (message,emoji,role,guild)"
                                             " VALUES (%s,%s,%s,%s)", (message.id, emoji, role.id, guild.id))
                        await cursor.execute("INSERT INTO restarter_roles (guild,role,alias) VALUES (%s,%s,%s)",
                                             (guild.id, role.id, channel.name))
                        await conn.commit()
                        counter += 1

            # Final message
            if message:
                if content:
                    await message.edit(content="\n".join(content))
                else:
                    await message.delete()
            await cursor.close()
            conn.close()

        # Done
        await ctx.send("Done")


    # Start the bot with token from token.txt
    with open("token" + ("_dev" if dev_mode else "") + ".txt", "r") as f:
        token = [str(f).strip("\n\r") for f in f.readlines()]
    bot.run(token[0], reconnect=False)

else:
    print("Run this by itself")
