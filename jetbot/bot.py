from __future__ import unicode_literals

import json
import logging
import os
import re
import traceback
from typing import Optional

from discord import Activity, ActivityType, Status, CategoryChannel, TextChannel, ForumChannel, StageChannel, Message, Intents, PermissionOverwrite, ChannelType, utils
from discord.ext import commands, tasks

from jetbot.config import Config

# Logging
logging.basicConfig(level=logging.ERROR)


class JetBrains(commands.Bot):

    def __init__(self, *args, **kwargs):
        self.data = []
        self.config = kwargs.pop("config")
        super().__init__(*args, **kwargs, command_prefix=commands.when_mentioned_or(*self.config.prefixes))

        self.load_data()
        self.create_commands_products()
        self.create_commands_extras()

    # Start the loops on boot
    async def setup_hook(self) -> None:
        self.status_loop.start()

    # Set the bot status once every five minutes
    @tasks.loop(minutes=5)
    async def status_loop(self):
        guild = self.get_guild(self.config.guild)
        if not guild:
            guild = await self.fetch_guild(self.config.guild)

        users = "{:,} ".format(guild.member_count) if guild else ""
        await self.change_presence(
            activity=Activity(type=ActivityType.watching, name=users + "JetBrains users"),
            status=Status.online)

    # Wait for bot to connect before running status loop
    @status_loop.before_loop
    async def before_status_loop(self):
        await self.wait_until_ready()

    # Load the latest data into the bot
    def load_data(self):
        with open("data.json") as fl:
            self.data = json.load(fl)

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

    # Find product channels
    async def product_channels(self, data: dict) -> list[TextChannel | ForumChannel | StageChannel]:
        channels = []
        if not data.get("category_name") or not data.get("channels"):
            return channels

        guild = self.get_guild(self.config.guild)
        if not guild:
            guild = await self.fetch_guild(self.config.guild)

        valid_channels = [c for c in guild.channels if isinstance(c, (TextChannel, ForumChannel, StageChannel))]

        for channel_config in data["channels"]:
            for channel in valid_channels:
                if channel.name == channel_config["name"] \
                        and channel.type == ChannelType[channel_config.get("type", "text")] \
                        and channel.category \
                        and channel.category.name.lower().strip() == data["category_name"].lower().strip():
                    channels.append(channel)
                    break

        return channels

    # Find an emoji
    async def product_emoji(self, name: str) -> str:
        if name:
            guild = self.get_guild(self.config.guild)
            if not guild:
                guild = await self.fetch_guild(self.config.guild)

            emojis = guild.emojis
            if not emojis:
                emojis = await guild.fetch_emojis()

            for emoji in emojis:
                if emoji.name == name:
                    return str(emoji)
        return ""

    # Find a category
    async def product_category(self, name: str) -> Optional[CategoryChannel]:
        if name:
            guild = self.get_guild(self.config.guild)
            if not guild:
                guild = await self.fetch_guild(self.config.guild)

            categories = guild.categories
            if not categories:
                categories = await guild.fetch_channels()
                categories = [f for f in categories if isinstance(f, CategoryChannel)]

            for category in categories:
                if category.name.lower().strip() == name.lower().strip():
                    return category
        return None

    # Main custom group
    def group_callback(self, data):
        async def func(ctx: commands.Context):
            message = [await self.product_emoji(data["emoji_name"]) + " **" + data["name"] + "**"]
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
            channels = await self.product_channels(data)
            if channels:
                if len(channels) == 1:
                    message.append("\N{PAGE FACING UP} Discord Channel: " + channels[0].mention +
                                 ("" if ctx.guild and ctx.guild.id == self.config.guild else " - Join with " +
                                                                                           self.config.invite))
                else:
                    message.append("\N{PAGE FACING UP} Discord Channels:")
                    for channel in channels:
                        desc = ""
                        if "channels" in data:
                            for ch_config in data["channels"]:
                                if ch_config["name"] == channel.name:
                                    desc = f" - {ch_config['description']}"
                                    break
                        message.append(f"• {channel.mention}{desc}" +
                                     ("" if ctx.guild and ctx.guild.id == self.config.guild else f" - Join with {self.config.invite}"))
            await ctx.send("\n".join(message))

        return func

    # Custom reddit callback
    def reddit_callback(self, data):
        async def func(ctx: commands.Context):
            message = [await self.product_emoji(data["emoji_name"]) + " " + data["name"] + " - Subreddit"]
            if data["subreddit"]:
                message.append("**" + self.reddit_url(data["subreddit"]) + "**")
            else:
                message.append("*Sorry, there isn't a known subreddit*")
            await ctx.send("\n".join(message))

        return func

    # GitHub custom callback
    def github_callback(self, data):
        async def func(ctx: commands.Context):
            message = [await self.product_emoji(data["emoji_name"]) + " " + data["name"] + " - GitHub"]
            if data["github"]:
                message.append("**" + self.github_url(data["github"]) + "**")
            else:
                message.append("*Sorry, there is no known github link*")
            await ctx.send("\n".join(message))

        return func

    # Custom product page callback
    def page_callback(self, data):
        async def func(ctx: commands.Context):
            message = [await self.product_emoji(data["emoji_name"]) + " " + data["name"] + " - Product Page"]
            if data["product_page"]:
                message.append("**" + self.product_url(data["product_page"]) + "**")
            else:
                message.append("*Sorry, no known product page was found*")
            await ctx.send("\n".join(message))

        return func

    # Issue tracker callback
    def issue_callback(self, data):
        async def func(ctx: commands.Context):
            message = [await self.product_emoji(data["emoji_name"]) + " " + data["name"] + " - Issue Tracker"]
            if data["issue_tracker"]:
                message.append("**" + self.issue_url(data["issue_tracker"]) + "**")
            else:
                message.append("*Sorry, there is no known issue tracker*")
            await ctx.send("\n".join(message))

        return func

    # Channel callback
    def channel_callback(self, data):
        async def func(ctx: commands.Context):
            message = [await self.product_emoji(data["emoji_name"]) + " " + data["name"] + " - Discord Channels"]
            channels = await self.product_channels(data)
            if channels:
                join_info = "" if ctx.guild and ctx.guild.id == self.config.guild else " - Join with " + self.config.invite
                for channel in channels:
                    desc = next((c["description"] for c in data["channels"] if c["name"] == channel.name), "")
                    message.append("**" + channel.mention + "** - " + desc + join_info)
            else:
                message.append("*Sorry, there are no channels available*")
            await ctx.send("\n".join(message))

        return func

    # Register all custom commands for products
    def create_commands_products(self):
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

    # Register all extra commands
    def create_commands_extras(self):
        @self.command(aliases=["info", "about", "invite", "add", "author", "owner", "server", "support", "jetbot", "jetbrains"])
        async def information(ctx: commands.Context):
            """
            JetBot & JetBrains Community Discord Server info
            """
            await ctx.send("\n".join([
                await self.product_emoji("jetbrainscommunity") + " **JetBrains Server Bot (JetBot)**",
                "*The bot responsible for providing information in, and managing, the JetBrains server.*",
                "View all the commands for JetBrains product and project inforamtion JetBot has in the help "
                "command `?help`.",
                "\N{LINK SYMBOL} You can use JetBot in your server, invite it with: <https://discord.com/"
                "oauth2/authorize?client_id=" + str(self.user.id) + "&scope=bot&permissions=8>.",
                "*JetBot was created and is maintained by v4#1503 but is also open source at <https://github.com/"
                "JetBrains-Community/discord>.*", "",
                await self.product_emoji("jetbrainscommunity") + " **JetBrains Community Discord Server**",
                "The community home of all the JetBrains products and projects on Discord.",
                "Are you currently a user of JetBrains products or projects?",
                "Would you like to learn more about what JetBrains offers and what licensing options there are?",
                "> Talk to fellow users of the JetBrains software packages and get help with problems you may "
                "have.",
                "> Chat with other developers, see what they're working on using JetBrains tools and bounce "
                "ideas around.",
                "\N{BLACK RIGHTWARDS ARROW} **Join the JetBrains Community Discord server: <" + self.config.invite +
                ">**", "", await self.product_emoji("jetbrains") + " **JetBrains s.r.o**",
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


        @self.group(aliases=["licensing", "buy", "shop", "store"],
                invoke_without_command=True, case_insensitive=True)
        async def license(ctx: commands.Context):
            """
            JetBrains product licensing options
            """
            await ctx.send("\n".join([
                await self.product_emoji("jetbrains") + " **JetBrains Product Licensing Options**",
                "", *license_t_student(),
                "", *license_t_opensource(),
                "", *license_t_personal(),
                "", *license_t_organization()
            ]))


        @license.command(name="student", aliases=["school"])
        async def license_student(ctx: commands.Context):
            """
            JetBrains student licensing info
            """
            await ctx.send("\n".join([
                await self.product_emoji("jetbrains") + " **JetBrains Student Licensing**",
                *license_t_student(False)
            ]))


        @self.command(help=license_student.help, aliases=license_student.aliases)
        async def student(ctx: commands.Context):
            await ctx.invoke(license_student)


        @license.command(name="opensource", aliases=["open", "os"])
        async def license_opensource(ctx: commands.Context):
            """
            JetBrains open source licensing info
            """
            await ctx.send("\n".join([
                await self.product_emoji("jetbrains") + " **JetBrains Open Source Licensing**",
                *license_t_opensource(False)
            ]))


        @self.command(help=license_opensource.help, aliases=license_opensource.aliases)
        async def opensource(ctx: commands.Context):
            await ctx.invoke(license_opensource)


        @license.command(name="personal", aliases=["normal", "home"])
        async def license_personal(ctx: commands.Context):
            """
            JetBrains personal licensing info
            """
            await ctx.send("\n".join([
                await self.product_emoji("jetbrains") + " **JetBrains Personal Licenses**",
                *license_t_personal(False)
            ]))


        @license.command(name="organization", aliases=["organisation", "business", "work"])
        async def license_organization(ctx: commands.Context):
            """
            JetBrains organization licensing info
            """
            await ctx.send("\n".join([
                await self.product_emoji("jetbrains") + " **JetBrains Organization Licenses**",
                *license_t_organization(False)
            ]))


        @self.command()
        @commands.check(self.admin_check)
        async def emoji(ctx: commands.Context):
            """
            Admin: Update emoji on the JetBrains server
            """
            guild = await self.fetch_guild(self.config.guild)
            new = []
            for item in self.data:
                if item["icon_path"] and item["emoji_name"]:
                    if not await self.product_emoji(item["emoji_name"]):
                        if os.path.isfile("icons/" + item["icon_path"]):
                            with open("icons/" + item["icon_path"], "rb") as f:
                                print("Creating icon... " + item["icon_path"])
                                await guild.create_custom_emoji(name=item["emoji_name"], image=f.read())
                            new.append(item["emoji_name"])
                    else:
                        print(item["icon_path"] + " icon already exists")

            # Done
            await ctx.send("Done\n" + "\n".join([await self.product_emoji(f) for f in new]))


        @self.command()
        @commands.check(self.admin_check)
        async def channels(ctx: commands.Context):
            """
            Admin: Update channels on the JetBrains server
            """
            guild = await self.fetch_guild(self.config.guild)
            channel_methods = {
                "text": lambda category: category.create_text_channel,
                "forum": lambda category: category.create_forum,
                "stage_voice": lambda category: category.create_stage_channel,
            }

            # Store all the categories we encounter
            categories = {}

            # Store any new channels we create
            new = []

            # Create product channels
            for item in self.data:
                if item["category_name"]:
                    # Get the category
                    if item["category_name"].lower().strip() in categories:
                        category = categories[item["category_name"].lower().strip()]
                    else:
                        category = await self.product_category(item["category_name"])
                        if not category:
                            print("Creating category... " + item["category_name"])
                            category = await guild.create_category(item["category_name"])
                        categories[item["category_name"].lower().strip()] = category

                    # Handle channels configuration
                    if item["channels"]:
                        existing_channels = await self.product_channels(item)
                        product_category = category.name.lower().strip()
                        product_emoji = await self.product_emoji(item["emoji_name"])

                        for channel_config in item["channels"]:
                            channel = None

                            # Attempt to find the channel
                            # Assumes that an item doesn't have two channels of the same name with different types
                            for existing in existing_channels:
                                if existing.name == channel_config["name"]:
                                    print("Found channel... " + channel_config["name"] + " in " + item["category_name"])
                                    channel = existing
                                    break

                            # Create the channel if it doesn't exist
                            if not channel:
                                print("Creating channel... " + channel_config["name"] + " in " + item["category_name"])
                                channel = await channel_methods[channel_config.get("type", "text")](category)(channel_config["name"])
                                new.append(channel)

                            # Create or update forum tags if it's a forum channel and has available_tags
                            if isinstance(channel, ForumChannel) and "available_tags" in channel_config:
                                print("Processing forum tags for... " + channel_config["name"])
                                # Get existing tags
                                existing_tags = [tag.name for tag in channel.available_tags]

                                for tag_name in channel_config["available_tags"]:
                                    # Skip if tag already exists
                                    if tag_name in existing_tags:
                                        print(f"Tag already exists: {tag_name}")
                                        continue

                                    try:
                                        await channel.create_tag(name=tag_name)
                                        print(f"Created tag: {tag_name}")
                                    except Exception as e:
                                        print(f"Failed to create tag {tag_name}: {str(e)}")
                                        continue

                            # Reset permissions
                            for overwrite in channel.overwrites:
                                print("Resetting channel permissions... " + channel_config["name"], overwrite)
                                await channel.set_permissions(overwrite, overwrite=None)

                            # Set basic channel settings
                            title = "{} - {}".format(item["name"], channel_config.get("description", item["description"]))
                            title = "{0} {1} {0}".format(product_emoji, title) if product_emoji else title
                            if channel.topic != title or channel.slowmode_delay != 5 or not channel.permissions_synced:
                                print("Updating channel settings... " + channel_config["name"])
                                await channel.edit(topic=title, slowmode_delay=5, sync_permissions=True)

                            # Handle permissions
                            if "permissions" in channel_config:
                                for permission_name, role_names in channel_config["permissions"].items():
                                    print(f"Removing {permission_name}... @everyone in {channel_config['name']}")
                                    # Create permission kwargs dynamically
                                    permission_kwargs = {permission_name: False}
                                    await channel.set_permissions(guild.default_role, **permission_kwargs)
                                    for role_name in role_names:
                                        role = utils.get(guild.roles, name=role_name)
                                        if role:
                                            print(f"Adding {permission_name}... {role_name} in {channel_config['name']}")
                                            permission_kwargs[permission_name] = True
                                            await channel.set_permissions(role, **permission_kwargs)

            # Set category perms
            for category in categories.values():
                for overwrite in category.overwrites:
                    print("Resetting category permissions... " + category.name, overwrite)
                    await category.set_permissions(overwrite, overwrite=None)

            # Done
            await ctx.send("Done\n" + "\n".join([f.mention for f in new]))

    # Check for admin commands
    def admin_check(self, ctx: commands.Context) -> bool:
        return ctx.author.id in self.config.admins

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
        guild = self.get_guild(self.config.guild)
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
                        channel = await self.product_channel("admin-chat", "admins")
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
        print(self.user.name)
        print(self.user.id)
        print("https://discord.com/oauth2/authorize?client_id=" + str(self.user.id) + "&scope=bot&permissions=8")
        print("------")

    def run(self):
        super().run(self.config.token)


if __name__ == "__main__":
    # Create the bot instance
    bot = JetBrains(config=Config, intents=Intents(emojis=True, guilds=True, guild_messages=True, message_content=True))
    bot.run()
