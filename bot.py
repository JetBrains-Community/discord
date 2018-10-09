from __future__ import unicode_literals

import logging
import os

import aiomysql
import discord
from discord.ext import commands

# Logging
logging.basicConfig(level=logging.ERROR)

if __name__ == '__main__':

    # Create the bot instance
    bot = commands.Bot(command_prefix="jb!")
    bot.remove_command('help')


    # Acknowledge bot is ready to go
    @bot.event
    async def on_ready():
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('------')


    # Generate all the emotes required
    @bot.command()
    @commands.check(lambda ctx: ctx.author.id == 193060889111298048)
    async def emoji(ctx: commands.Context):
        current = {f.name.lower().strip(): f for f in ctx.guild.emojis}
        icons = os.listdir('icons')
        for icon in list(sorted(icons.copy(), key=lambda x: x.lower().strip())):
            if icon.endswith(".png") and icon.startswith("icon_"):
                iconname = icon.split("icon_", 1)[1].split(".png", 1)[0].replace("_", "").replace(
                    "-", "").lower().strip()
                if not iconname in current.keys():
                    print(icon, iconname)
                    with open('icons/' + icon, 'rb') as f:
                        await ctx.guild.create_custom_emoji(name=iconname, image=f.read())
        await ctx.send("Done")


    # Create all relevant roles (requires emotes to be created)
    @bot.command()
    @commands.check(lambda ctx: ctx.author.id == 193060889111298048)
    async def roles(ctx: commands.Context):
        # color = discord.Colour(0x18d68c)  # Normal
        color = discord.Colour(0xFB5502)  # Halloween
        # Create product roles
        current = {f.name.lower().strip(): f for f in ctx.guild.emojis}
        roles = {f.name.strip(): f for f in ctx.guild.roles}
        positions = []
        icons = os.listdir('icons')
        for icon in list(sorted(icons.copy(), key=lambda x: x.lower().strip())):
            if icon.endswith(".png") and icon.startswith("icon_"):
                iconname = icon.split("icon_", 1)[1].split(".png", 1)[0].replace("_", "").replace(
                    "-", "").lower().strip()
                if iconname in current.keys():
                    rolename = icon.split("icon_", 1)[1].split(".png", 1)[0].replace("_", " ").strip()
                    if rolename not in roles.keys():
                        print(icon, 1)
                        await ctx.guild.create_role(name=rolename, permissions=discord.Permissions.none(), color=color,
                                                    hoist=False, mentionable=False)
                    else:
                        print(icon, 2)
                        role = roles[rolename]
                        if role.color != color:
                            print(icon, 2.1)
                            await role.edit(color=color)
                    positions.append(role.position)
        # Create hide role
        if "Hide Unsubscribed Channels" not in roles.keys():
            print(3.1)
            role = await ctx.guild.create_role(name="Hide Unsubscribed Channels",
                                               permissions=discord.Permissions.none(),
                                               color=color, hoist=False, mentionable=False)
        else:
            role = roles["Hide Unsubscribed Channels"]
        positions = min(positions)
        if role.position != positions:
            print(3.2)
            await role.edit(position=positions)
        await ctx.send("Done")


    # Create all relevant channels (requires roles and emotes to be created)
    @bot.command()
    @commands.check(lambda ctx: ctx.author.id == 193060889111298048)
    async def channels(ctx: commands.Context):
        categories = [f.name.lower().strip() for f in ctx.guild.categories]
        if 'products' not in categories:
            await ctx.guild.create_category("Products")
        if 'open source' not in categories:
            await ctx.guild.create_category("Open Source")
        categories = {f.name.lower().strip(): f for f in ctx.guild.categories}
        default_category = categories['products']
        category_map = {'open source': ["intellij-community", "kotlin", "ring-ui", "mps"]}
        await default_category.set_permissions(ctx.guild.default_role, send_messages=False)
        for key in category_map.keys():
            if key in categories.keys():
                await categories[key].set_permissions(ctx.guild.default_role, send_messages=False)
        default_title = "Discuss anything about {} here."
        title_map = {'open source': "Chat about the open source project {} here."}
        mods = [f for f in ctx.guild.roles if f.name.lower().strip() == '-']
        if mods:
            mods = mods[0]
            await default_category.set_permissions(mods, send_messages=True)
            for key in category_map.keys():
                if key in categories.keys():
                    await categories[key].set_permissions(mods, send_messages=True)
        hide = [f for f in ctx.guild.roles if f.name.strip() == 'Hide Unsubscribed Channels'][0]
        current = {f.name.lower().strip(): f for f in ctx.guild.emojis}
        roles = {f.name.strip(): f for f in ctx.guild.roles}
        icons = os.listdir('icons')
        for icon in list(sorted(icons.copy(), key=lambda x: x.lower().strip())):
            print(icon, 0)
            if icon.endswith(".png") and icon.startswith("icon_"):
                iconname = icon.split("icon_", 1)[1].split(".png", 1)[0].replace("_", "").replace(
                    "-", "").lower().strip()
                if iconname in current.keys():
                    rolename = icon.split("icon_", 1)[1].split(".png", 1)[0].replace("_", " ").strip()
                    if rolename in roles.keys():
                        print(icon, 1)
                        category = [k for k, v in category_map.items() if rolename.lower().replace(" ", "-") in v]
                        category = categories[category[0]] if category and category[
                            0] in categories.keys() else default_category
                        channels = {f.name.lower().strip(): f for f in ctx.guild.text_channels if
                                    f.category and f.category == category}
                        if rolename.lower().replace(" ", "-") not in channels.keys():
                            channel = await ctx.guild.create_text_channel(rolename.lower().replace(" ", "-"),
                                                                          category=category)
                            print(icon, 2.1)
                        else:
                            channel = channels[rolename.lower().replace(" ", "-")]
                        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
                        role = roles[rolename]
                        await channel.set_permissions(role, send_messages=True, read_messages=True)
                        await channel.set_permissions(hide, read_messages=False)
                        if mods:
                            await channel.set_permissions(mods, send_messages=True, read_messages=True)
                            print(icon, 2.2)
                        title = title_map[category.name.lower().strip()] if category.name.lower().strip() in \
                                                                            title_map.keys() else default_title
                        title = "{0} \N{PUBLIC ADDRESS LOUDSPEAKER} Unlock this channel using #unlock-channels - {1} " \
                                "{0}".format(str(current[iconname]), title.format(rolename))
                        if channel.topic != title:
                            await channel.edit(topic=title)
                            print(icon, 2.3)
                        print(icon, 2)
        await ctx.send("Done")


    # Create all relevant react roles (requires channels, roles and emotes to be created)
    @bot.command()
    @commands.check(lambda ctx: ctx.author.id == 193060889111298048)
    async def reactions(ctx: commands.Context):
        categories = {f.name.lower().strip(): f for f in ctx.guild.categories}
        if 'information' in categories.keys() and 'general' in categories.keys():
            category = categories['information']
            category_general = categories['general']
            current = {f.name.lower().strip(): f for f in ctx.guild.emojis}
            roles = {f.name.strip(): f for f in ctx.guild.roles}
            channels = {f.name.lower().strip(): f for f in ctx.guild.text_channels if
                        f.category and (f.category == category or f.category == category_general)}
            if 'unlock-channels' not in channels.keys():
                channel = await ctx.guild.create_text_channel('unlock-channels', category=category)
            else:
                channel = channels['unlock-channels']
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            async for message in channel.history(limit=None):
                await message.delete()
            offtopic = channels['off-topic']
            await channel.send("**React to the following messages with JetBrains product and project emoji to unlock "
                               "the relevant discussion channels in this server.**\n\nClick on one of the reactions "
                               "already on the messages to unlock the role. Remove your reaction to remove your role."
                               "\n\nReactions not working for you? Head over to {} and type `r.roles` to use commands "
                               "instead.".format(offtopic.mention))
            # Create db connection for Restarter's react roles from db.txt
            with open("db.txt", "r") as f:
                db = [str(f).strip("\n\r") for f in f.readlines()]
            conn = await aiomysql.connect(host=db[0], port=3306, user=db[1], password=db[2], db=db[3], loop=bot.loop)
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM restarter_reactroles WHERE guild = %s", (ctx.guild.id))
            await cursor.execute("DELETE FROM restarter_roles WHERE guild = %s", (ctx.guild.id))
            await conn.commit()
            data = []
            channels = {f.name.lower().strip(): f for f in ctx.guild.text_channels if
                        f.category and (f.category.name.lower().strip() in ["products", "open source"])}
            icons = os.listdir('icons')
            for icon in list(sorted(icons.copy(), key=lambda x: x.lower().strip())):
                if icon.endswith(".png") and icon.startswith("icon_"):
                    iconname = icon.split("icon_", 1)[1].split(".png", 1)[0].replace("_", "").replace(
                        "-", "").lower().strip()
                    if iconname in current.keys():
                        rolename = icon.split("icon_", 1)[1].split(".png", 1)[0].replace("_", " ").strip()
                        if rolename in roles.keys():
                            role = roles[rolename]
                            if rolename.lower().replace(" ", "-") in channels.keys():
                                print(icon, 0)
                                # channel, emoji, role, rolename, icon name
                                data.append([channels[rolename.lower().replace(" ", "-")], current[iconname], role,
                                             rolename.replace(" ", "-"), icon])

            async def do_res_role(role_id: int, guild_id: int, message_id: int, emoji: str, alias: str):
                await cursor.execute("INSERT INTO restarter_reactroles (message,emoji,role,guild)"
                                     " VALUES (%s,%s,%s,%s)", (message_id, emoji, role_id, guild_id))
                await cursor.execute("INSERT INTO restarter_roles (guild,role,alias) VALUES (%s,%s,%s)",
                                     (guild_id, role_id, alias))
                await conn.commit()

            """
            message = await channel.send("Want to hide the channels you aren't active in? Mute the channels by right "
                                         "clicking and ticking mute (click the channel name on mobile and open "
                                         "notification settings to mute it). Once the channels are muted right click "
                                         "on the channel list and tick Hide Muted Channels to make them disappear (on "
                                         "mobile, press the server name and then use the Hide Muted Channels option "
                                         "shown).")
            """
            message = await channel.send("Want to hide the channels you aren't active in? React to this message with "
                                         "\N{NO ENTRY SIGN} to hide any product channel you aren't 'subscribed' to "
                                         "using the roles below. Remove your reaction to show all JetBrains product "
                                         "channels again. Can't use reactions, head to {} and use 'r.hide' to toggle "
                                         "the role.".format(offtopic.mention))
            await message.add_reaction("\N{NO ENTRY SIGN}")
            await do_res_role(roles["Hide Unsubscribed Channels"].id, ctx.guild.id, message.id,
                              "\N{NO ENTRY SIGN}".encode('ascii', 'namereplace').decode(), "hide")
            counter = 0
            message = None
            content = []
            for item in data:
                print(item[4], 1)
                if counter % 5 == 0:
                    if message:
                        await message.edit(content="\n".join(content))
                        content = []
                    message = await channel.send("Placeholder")
                counter += 1
                content.append(str(item[1]) + " - " + item[0].mention)
                await message.add_reaction(item[1])
                await do_res_role(item[2].id, ctx.guild.id, message.id, str(item[1]), item[3])
            await cursor.close()
            conn.close()
            if message and content:
                await message.edit(content="\n".join(content))
        await ctx.send("Done")


    # Start the bot with token from token.txt
    with open("token.txt", "r") as f:
        token = [str(f).strip("\n\r") for f in f.readlines()]
    bot.run(token[0])

else:
    print('Run this by itself')
