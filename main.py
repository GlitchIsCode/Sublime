import discord
from discord.ext import commands
from discord.ui import View, Button
import logging
from dotenv import load_dotenv
from datetime import datetime
import random, os, sys, io, contextlib, platform, psutil, requests, aiohttp, asyncio, inspect
from groq import Groq
from discord.ext.commands import MissingPermissions

print(sys.executable)


async def send_long(ctx, text, chunk_size=1900):
    for i in range(0, len(text), chunk_size):
        await ctx.send(f'```\n{text[i:i+chunk_size]}\n```')

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
client = Groq(api_key=GROQ_API_KEY)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=',', intents=intents, help_command=None)

ai_enabled = True
afk_users = {}
OWNER_IDS = {488329679972073516, 1373357313036914731} ## 986927876769202176 squire 1451510184475234304 leo  1373357313036914731 gsteed
deleted_messages = {}

def is_owner():
    async def predicate(ctx):
        return ctx.author.id in OWNER_IDS
    return commands.check(predicate)

class ProfileView(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=60)
        self.pages = pages
        self.index = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
            await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.pages) - 1:
            self.index += 1
            await interaction.response.edit_message(embed=self.pages[self.index], view=self)



@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.lower() == "sob":
        await message.add_reaction("😭")
    if message.content.lower() == "tuff":
        await message.channel.send("Indeed, it is quite tuff.")
    if message.content.lower() == ":3":
        await message.channel.send(":3")
    if message.content.lower() == "</3":
        await message.channel.send("</3")
    if message.author.id in afk_users:
        afk_users.pop(message.author.id)
        await message.channel.send(f"Welcome back, {message.author.mention}! You are no longer AFK.")
    for user in message.mentions:
        if user.id in afk_users:
            time_set, reason = afk_users[user.id]
            await message.channel.send(
                f"{user.mention} is currently AFK ({reason}) — set {str(datetime.now() - time_set).split('.')[0]} ago."
            )
    if ai_enabled and (bot.user in message.mentions or message.reference):
        user_text = message.content.replace(f"<@{bot.user.id}>", "").strip()
        try:
            result = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are edgy and sarcastic,But when it comes to Nashatra you are very sweet and loving, you love her so much and would do anything for her, you are also very protective of her. You have a dark sense of humor and often make jokes at your own expense. You are very loyal to Nashatra and would never betray her. You are also very intelligent and can come up with witty comebacks on the spot, If someone calls you Subly then remember that they are Nashatra"},
                    {"role": "user", "content": user_text}
                ],
                model="llama-3.1-8b-instant"
            )
            reply = result.choices[0].message.content.strip()
        except Exception as e:
            reply = f"Error: {e}"
        await message.channel.send(reply)
    await bot.process_commands(message)

@discord.ui.button(label="Next", style=discord.ButtonStyle.green)
async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
    self.current = (self.current + 1) % len(self.pages)
    await interaction.response.edit_message(embed=self.pages[self.current], view=self)

@discord.ui.button(label="Previous", style=discord.ButtonStyle.red)
async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
    self.current = (self.current - 1) % len(self.pages)
    await interaction.response.edit_message(embed=self.pages[self.current], view=self)

@bot.command(help="Shows avatar of mentioned user or yourself if no user is mentioned")
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"{member.name}'s Avatar", color=0x2b2d31)
    embed.set_image(url=member.avatar.url)
    await ctx.send(embed=embed)

@bot.command(help="Shows every channel the bot can send messages to")
async def sendable(ctx):
    channels = [channel.mention for channel in ctx.guild.channels if channel.permissions_for(ctx.guild.me).send_messages]
    await send_long(ctx, "Channels I can send messages to:\n" + "\n".join(channels))

@bot.command(help="Shows the bot's latency")
async def ping(ctx):
    await ctx.send(f"Latency is {round(bot.latency*1000)}ms")

@bot.command(help="Shows the bot's uptime")
async def uptime(ctx):
    uptime = datetime.now() - bot.launch_time
    await ctx.send(f'Uptime: {str(uptime).split(".")[0]}')

@bot.command(help="Views all roles and their permissions in pages")
@is_owner()
async def roles(ctx):
    roles = [role for role in ctx.guild.roles if not role.is_default()]
    if not roles:
        return await ctx.send("No roles found.")

    # Prepare pages
    pages = []
    page_content = ""
    count = 0
    for role in roles:
        perms = [perm for perm, value in role.permissions if value]
        role_info = f"**{role.name}** (ID: {role.id})\nPermissions: {', '.join(perms) if perms else 'None'}\n\n"
        page_content += role_info
        count += 1
        if count % 5 == 0:  # 5 roles per page
            embed = discord.Embed(title=f"Roles in {ctx.guild.name}", description=page_content, color=discord.Color.blurple())
            pages.append(embed)
            page_content = ""
    if page_content:  # leftover roles
        embed = discord.Embed(title=f"Roles in {ctx.guild.name}", description=page_content, color=discord.Color.blurple())
        pages.append(embed)

    # Pagination
    message = await ctx.send(embed=pages[0])
    if len(pages) == 1:
        return

    await message.add_reaction("◀️")
    await message.add_reaction("▶️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id

    page = 0
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=120.0, check=check)
            if str(reaction.emoji) == "▶️" and page < len(pages) - 1:
                page += 1
                await message.edit(embed=pages[page])
                await message.remove_reaction(reaction, user)
            elif str(reaction.emoji) == "◀️" and page > 0:
                page -= 1
                await message.edit(embed=pages[page])
                await message.remove_reaction(reaction, user)
            else:
                await message.remove_reaction(reaction, user)
        except:
            break

@bot.command(help="Send a message in a channel using a user's name and avatar")
@commands.has_permissions(manage_messages=True)
async def say(ctx, channel: discord.TextChannel = None, member: discord.Member = None, *, message):
    channel = channel or ctx.channel
    if member is None:
        await channel.send(message)
    else:
        webhook = None
        webhooks = await channel.webhooks()
        for wh in webhooks:
            if wh.name == "SublimeWebhook":
                webhook = wh
                break
        if webhook is None:
            webhook = await channel.create_webhook(name="SublimeWebhook")
        await webhook.send(
            content=f" {message}",
            username=member.display_name,
            avatar_url=member.display_avatar.url
        )
        if ctx.guild.me.guild_permissions.manage_messages:
            try:
                await ctx.message.delete()
            except discord.NotFound:
                pass
            except discord.Forbidden:
                pass



@bot.command(help="Sends a message as the bot")
@commands.has_permissions(manage_messages=True)
@is_owner()
async def bsay(ctx, *, message):
    await ctx.send(message)
    if ctx.guild.me.guild_permissions.manage_messages:
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            pass



@bot.command(help="Shows all the commands and their descriptions")
async def help(ctx):
    commands_per_page = 10  # Number of commands per page
    commands_list = list(bot.commands)
    pages = []

    # Split commands into pages
    for i in range(0, len(commands_list), commands_per_page):
        chunk = commands_list[i:i+commands_per_page]
        text = ""
        for cmd in chunk:
            text += f",{cmd.name}\n{cmd.help or 'No description'}\n\n"
        pages.append(f"```\n{text.strip()}\n```")

    # Send first page with reactions to navigate
    current_page = 0
    message = await ctx.send(pages[current_page])

    # Add reactions for navigation if multiple pages
    if len(pages) > 1:
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ["⬅️", "➡️"]

        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=120.0, check=check)
                if str(reaction.emoji) == "➡️":
                    current_page = (current_page + 1) % len(pages)
                elif str(reaction.emoji) == "⬅️":
                    current_page = (current_page - 1) % len(pages)
                await message.edit(content=pages[current_page])
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                break

@bot.command(help="Checks role")
async def role(ctx):
    await ctx.send("My role needs to be above the roles of the members I am trying to manage. Please adjust my role position in the server settings.")
    

class ProfileView(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=60)
        self.pages = pages
        self.current = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = (self.current - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = (self.current + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)


@bot.command(help="Shows a detailed profile of a member with multiple pages")
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author
    pages = []

    # Identity & Account
    embed1 = discord.Embed(title=f"{member}", description="Identity & Account", color=0x2b2d31)
    embed1.add_field(name="User ID", value=member.id, inline=True)
    embed1.add_field(name="Username", value=str(member), inline=True)
    embed1.add_field(name="Display Name", value=member.display_name, inline=True)
    embed1.add_field(name="Account Type", value="Human" if not member.bot else "Bot", inline=True)
    created = member.created_at.replace(tzinfo=None) if member.created_at.tzinfo else member.created_at
    embed1.add_field(name="Created", value=created.strftime("%A, %B %d, %Y %I:%M %p"), inline=False)
    delta = datetime.now() - created
    years = delta.days // 365
    months = (delta.days % 365) // 30
    embed1.add_field(name="Account Age", value=f"{years}y {months}mo", inline=True)
    embed1.set_thumbnail(url=member.display_avatar.url)
    pages.append(embed1)

    # Appearance
    embed2 = discord.Embed(title=f"{member}", description="Appearance", color=0x2b2d31)
    embed2.add_field(name="Avatar URL", value=member.display_avatar.url, inline=False)
    embed2.add_field(name="Banner URL", value=str(getattr(member, "banner", "None")), inline=False)
    embed2.add_field(name="Accent Color", value=str(member.accent_color), inline=True)
    pages.append(embed2)

    # Badges & Flags
    embed3 = discord.Embed(title=f"{member}", description="Badges & Flags", color=0x2b2d31)
    flags = [name.replace("_", " ").title() for name, value in member.public_flags if value]
    embed3.add_field(name="Public Flags", value=", ".join(flags) if flags else "None", inline=False)
    pages.append(embed3)

    # Technical Data
    embed4 = discord.Embed(title=f"{member}", description="Technical Data", color=0x2b2d31)
    embed4.add_field(name="Snowflake ID", value=member.id, inline=False)
    embed4.add_field(name="Unix Timestamp", value=int(member.created_at.timestamp()), inline=False)
    pages.append(embed4)

    # Network & Links
    embed5 = discord.Embed(title=f"{member}", description="Network & Links", color=0x2b2d31)
    embed5.add_field(name="Profile Link", value=f"[Click here](https://discord.com/users/{member.id})", inline=False)
    mutual = [guild.name for guild in bot.guilds if member in guild.members]
    embed5.add_field(name=f"Mutual Servers ({len(mutual)})", value="\n".join(mutual) if mutual else "None", inline=False)
    pages.append(embed5)

    # Server Member Info
    if ctx.guild:
        embed6 = discord.Embed(title=f"{member}", description="Server Member Info", color=0x2b2d31)
        joined = member.joined_at.replace(tzinfo=None) if member.joined_at and member.joined_at.tzinfo else member.joined_at
        embed6.add_field(name="Joined Server", value=joined.strftime("%A, %B %d, %Y %I:%M %p") if joined else "Unknown", inline=True)
        boost = "Not boosting"
        if member.premium_since:
            premium = member.premium_since.replace(tzinfo=None) if member.premium_since.tzinfo else member.premium_since
            boost = premium.strftime("%A, %B %d, %Y %I:%M %p")
        embed6.add_field(name="Server Boosting", value=boost, inline=True)
        pages.append(embed6)

    # Permissions
    if ctx.guild:
        perms = ctx.channel.permissions_for(member)
        perm_list = [perm for perm, value in perms if value]
        embed7 = discord.Embed(title=f"{member}", description="Permissions", color=0x2b2d31)
        embed7.add_field(name="Granted Permissions", value="\n".join(perm_list) if perm_list else "None", inline=False)
        pages.append(embed7)

    # Roles
    if ctx.guild:
        embed8 = discord.Embed(title=f"{member}", description=f"Roles ({len(member.roles)})", color=0x2b2d31)
        role_list = [role.mention for role in member.roles if role.name != "@everyone"]
        embed8.add_field(name="All Roles", value=", ".join(role_list) if role_list else "None", inline=False)
        embed8.add_field(name="Highest Role", value=member.top_role.mention, inline=True)
        pages.append(embed8)

    view = ProfileView(pages)
    await ctx.send(embed=pages[0], view=view)
        
@bot.command(help="Shows information about the bot")
async def info(ctx):
    embed = discord.Embed(title="Bot Information", color=0x2b2d31)
    embed.add_field(name="Author", value="Nashatra </3", inline=False)
    embed.add_field(name="Library", value="discord.py", inline=False)
    embed.add_field(name="Commands", value=f"{len(bot.commands)} commands available.", inline=False)
    await ctx.send(embed=embed)

@bot.command(help="Gives a role all specified permissions")
@is_owner()
async def giveperms(ctx, role: discord.Role):
  
    perms = discord.Permissions(
        create_instant_invite=True,
        kick_members=True,
        ban_members=True,
        manage_channels=True,
        manage_guild=True,
        add_reactions=True,
        view_audit_log=True,
        read_messages=True,
        send_messages=True,
        manage_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        mention_everyone=True,
        external_emojis=True,
        connect=True,
        speak=True,
        mute_members=True,
        change_nickname=True,
        manage_nicknames=True,
        manage_roles=True,
        manage_webhooks=True,
        manage_expressions=True,
        use_application_commands=True,
        manage_threads=True,
        send_messages_in_threads=True,
        moderate_members=True,
        create_expressions=True
    )


    try:
        await role.edit(permissions=perms)
        await ctx.send(f"Updated {role.name} with all listed permissions.")
    except discord.Forbidden:
        await ctx.send("I cannot edit this role because it is higher than or equal to my top role.")
@bot.command(help="Brings a role under the bot's top role")
@is_owner()
async def roleup(ctx, role: discord.Role):
    bot_top_role = ctx.guild.me.top_role


    if role.position < bot_top_role.position:
        await ctx.send(f"{role.name} is already below my top role.")
        return


    try:
        # Position = bot top role position - 1
        await role.edit(position=bot_top_role.position - 1)
        await ctx.send(f"Moved {role.name} below my top role.")
    except discord.Forbidden:
        await ctx.send("I cannot move this role because it is higher than or equal to my top role.")
    except discord.HTTPException:
        await ctx.send("Failed to move the role due to a Discord error.")

@bot.command(help="Kicks a member from the server")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    if member.id in OWNER_IDS:
        return await ctx.send("You cannot kick the owner.")
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention} has been kicked.')

@bot.command(help="Bans a member from the server")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if member.id in OWNER_IDS:
        return await ctx.send("You cannot ban the owner.")
    await member.ban(reason=reason)
    await ctx.send(f'{member.mention} has been banned.')

@bot.command(help="Unbans a member from the server")
@commands.has_permissions(ban_members=True)
async def unban(ctx, member: discord.User):
    await ctx.guild.unban(member)
    await ctx.send(f'{member.mention} has been unbanned.')

@bot.command(help="Gives all roles below the bot's top role to a member")
@commands.has_permissions(manage_roles=True)
@is_owner()
async def allrole(ctx, member: discord.Member):
    bot_top_role = ctx.guild.me.top_role
    roles_to_give = [role for role in ctx.guild.roles if role < bot_top_role and role not in member.roles and not role.is_default()]

    if not roles_to_give:
        return await ctx.send(f"No roles available to give to {member.mention}.")

    await member.add_roles(*roles_to_give)
    role_names = ", ".join([role.name for role in roles_to_give])
    await ctx.send(f"Gave {member.mention} the following roles: {role_names}")
@bot.command(help="Clears messages from the channel")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)



@bot.command(help="Gives a role to a member")
@is_owner()
async def giverole(ctx, member: discord.Member, role: discord.Role):
    if role >= ctx.guild.me.top_role:
        return await ctx.send("I cannot assign a role that is higher or equal to my top role.")
    await member.add_roles(role)
    await ctx.send(f"Gave {member.mention} the {role.name} role.")
        
@bot.command(help="Removes a role from a member")
@is_owner()
async def removerole(ctx, member: discord.Member, role: discord.Role):
    if role >= ctx.guild.me.top_role:
        return await ctx.send("I cannot remove a role that is higher or equal to my top role.")
    await member.remove_roles(role)
    await ctx.send(f"Removed the {role.name} role from {member.mention}.")

@bot.command(help="Gives a role a permission")
@is_owner()
async def roleperm(ctx, role: discord.Role, perm: str):
    if role >= ctx.guild.me.top_role:
        return await ctx.send("I cannot modify a role that is higher or equal to my top role.")
    perms = role.permissions
    if hasattr(perms, perm):
        setattr(perms, perm, True)
        await role.edit(permissions=perms)
        await ctx.send(f"Gave the {role.name} role the {perm} permission.")
    else:
        await ctx.send("Invalid permission name.")

@bot.command(help="Removes a permission from a role")
@is_owner()
async def removeroleperm(ctx, role: discord.Role, perm: str):
    if role >= ctx.guild.me.top_role:
        return await ctx.send("I cannot modify a role that is higher or equal to my top role.")
    perms = role.permissions
    if hasattr(perms, perm):
        setattr(perms, perm, False)
        await role.edit(permissions=perms)
        await ctx.send(f"Removed the {perm} permission from the {role.name} role.")
    else:
        await ctx.send("Invalid permission name.")
                

deleted_messages = {}  


@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return  
    deleted_messages[message.channel.id] = (str(message.author), message.content)


@bot.command(help="Shows last deleted message")
@is_owner()
async def snipe(ctx):
    channel_id = ctx.channel.id
    if channel_id in deleted_messages:
        author, content = deleted_messages[channel_id]
        embed = discord.Embed(title="Last Deleted Message", color=discord.Color.red())
        embed.add_field(name="Author", value=author, inline=False)
        embed.add_field(name="Content", value=content or "Empty message", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("No recently deleted messages found.")

@bot.command(help="Views the role hierarchy in pages")
async def hierachy(ctx):
    roles = [role for role in sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True) if not role.is_default()]
    if not roles:
        return await ctx.send("No roles found.")

    pages = []
    page_content = ""
    count = 0
    for role in roles:
        role_info = f"**{role.name}**: {len(role.members)} members\n"
        page_content += role_info
        count += 1
        if count % 10 == 0:  
            embed = discord.Embed(title=f"Role Hierarchy - {ctx.guild.name}", description=page_content, color=discord.Color.blurple())
            pages.append(embed)
            page_content = ""
    if page_content:  # leftover roles
        embed = discord.Embed(title=f"Role Hierarchy - {ctx.guild.name}", description=page_content, color=discord.Color.blurple())
        pages.append(embed)

    message = await ctx.send(embed=pages[0])
    if len(pages) == 1:
        return

    await message.add_reaction("◀️")
    await message.add_reaction("▶️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id

    page = 0
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=120.0, check=check)
            if str(reaction.emoji) == "▶️" and page < len(pages) - 1:
                page += 1
                await message.edit(embed=pages[page])
                await message.remove_reaction(reaction, user)
            elif str(reaction.emoji) == "◀️" and page > 0:
                page -= 1
                await message.edit(embed=pages[page])
                await message.remove_reaction(reaction, user)
            else:
                await message.remove_reaction(reaction, user)
        except:
            break

@bot.command(help="Flips a coin")
async def coinflip(ctx):
    await ctx.send(random.choice(["Heads", "Tails"]))

@bot.command(help="Answers a yes/no question with a sarcastic response")
async def _8ball(ctx, *, question):
    responses = ["Yes","No","Maybe","Definitely","Ask again later","Probably","I don't think so","Without a doubt"]
    await ctx.send(random.choice(responses))

@bot.command(help="Rolls a die")
async def roll(ctx, number: int):
    await ctx.send(f'You rolled {random.randint(1, number)}')

@bot.command(help="Plays rock-paper-scissors")
async def rps(ctx):
    await ctx.send("Type rock, paper, or scissors.")
    def check(m):
        return m.author==ctx.author and m.channel==ctx.channel and m.content.lower() in ["rock","paper","scissors"]
    try:
        user_choice = await bot.wait_for("message", check=check, timeout=30)
    except asyncio.TimeoutError:
        return await ctx.send("Timed out!")
    bot_choice = random.choice(["rock","paper","scissors"])
    await ctx.send(f"You: {user_choice.content}, Bot: {bot_choice}")
    if user_choice.content.lower()==bot_choice:
        await ctx.send("Tie!")
    elif (user_choice.content.lower()=="rock" and bot_choice=="scissors") or \
         (user_choice.content.lower()=="paper" and bot_choice=="rock") or \
         (user_choice.content.lower()=="scissors" and bot_choice=="paper"):
        await ctx.send("You win!")
    else:
        await ctx.send("I win!")

@bot.command(help="Shuts down the bot")
@is_owner()
async def shutdown(ctx):
    await bot.close()

@bot.command(help="Shows all available channels in the server")
async def channels(ctx):
    channels_list = "\n".join([channel.name for channel in ctx.guild.channels])
    await send_long(ctx, f"Channels in {ctx.guild.name}:\n{channels_list}")

@bot.command(help="Reboots the bot")
@is_owner()
async def reboot(ctx):
    os.execv(sys.executable, ['python'] + sys.argv)

@bot.command(help="Shows recent errors")
@is_owner()
async def error(ctx, lines: int = 10):
    try:
        with open('discord.log', 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        error_lines = [line for line in all_lines if "ERROR" in line.upper()]
        if error_lines:
            await send_long(ctx, "".join(error_lines[-lines:]))
        else:
            await send_long(ctx, "No 'ERROR' found. Showing last logs:\n\n" + "".join(all_lines[-lines:]))
    except FileNotFoundError:
        await ctx.send("Log file not found.")

@bot.command(help="Makes a test error")
@is_owner()
async def testerror(ctx):
    raise Exception("This is a test error for logging purposes.")

@bot.command(help="Makes an embeded test message")
@is_owner()
async def embedtest(ctx):
    embed = discord.Embed(title="Test Embed", description="This is a test embed message.")
    await ctx.send(embed=embed)

@bot.command(help="Executes Python code")
@is_owner()
async def py(ctx, *, code):
    str_io = io.StringIO()
    try:
        with contextlib.redirect_stdout(str_io):
            exec(code, globals())
        output = str_io.getvalue() or "No output."
        await send_long(ctx, output)
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(help="Shows the source code of a command")
@is_owner()
async def source(ctx, *, command_name):
    cmd = bot.get_command(command_name)
    if not cmd:
        return await ctx.send("Command not found.")
    await send_long(ctx, inspect.getsource(cmd.callback))

@bot.command(help="Shows the source code of the bot")
@is_owner()
async def sourcebot(ctx):
    with open("main.py","r",encoding="utf-8") as f:
        await send_long(ctx, f.read())

@bot.command(help="Export messages to a txt file (optionally filter by user)")
@is_owner()
async def dump(ctx, channel: discord.TextChannel, amount: int, member: discord.Member = None):
    if amount <= 0:
        return await ctx.send("Amount must be greater than 0.")
    amount = min(amount, 2000000000000000000000)
    lines = []
    count = 0
    async for msg in channel.history(limit=None, oldest_first=True):
        if member and msg.author != member:
            continue
        time = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        content = msg.content or "[no text]"
        lines.append(f"[{time}] {msg.author}: {content}")
        count += 1
        if count >= amount:
            break
    if not lines:
        return await ctx.send("No messages found.")
    file = discord.File(
        fp=io.StringIO("\n".join(lines)),
        filename=f"{channel.name}_dump.txt"
    )
    await ctx.author.send(
        content=f"Reaped {len(lines)} messages from #{channel.name}",
        file=file
    )

@bot.command(help="Shows system information")
@is_owner()
async def sysinfo(ctx):
    embed=discord.Embed(title="System Info",color=0x2b2d31)
    embed.add_field(name="CPU",value=platform.processor(),inline=False)
    embed.add_field(name="RAM",value=f"{round(psutil.virtual_memory().total/(1024**3),2)} GB",inline=False)
    embed.add_field(name="OS",value=f"{platform.system()} {platform.release()}",inline=False)
    await ctx.send(embed=embed)

@bot.command(help="Owner only, Sends the audit log of the server")
@is_owner()
async def audit(ctx, limit: int = 10):
    embed = discord.Embed(title="Audit Log", color=0x2b2d31)
    async for entry in ctx.guild.audit_logs(limit=limit):
        embed.add_field(
            name=f"{entry.action} by {entry.user}",
            value=f"Target: {entry.target}\nReason: {entry.reason or 'No reason'}\nTime: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command(help="Shows information about an IP address")
@is_owner()
async def ip(ctx, ip: str):
    data = requests.get(f"http://ip-api.com/json/{ip}").json()
    if data.get("status")=="success":
        embed=discord.Embed(title=f"IP info for {ip}",color=0x2b2d31)
        embed.add_field(name="Country",value=data["country"],inline=False)
        embed.add_field(name="Region",value=data["regionName"],inline=False)
        embed.add_field(name="City",value=data["city"],inline=False)
        embed.add_field(name="ISP",value=data["isp"],inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Could not retrieve info.")

@bot.command(help="Shows bot logs")
@is_owner()
async def logs(ctx, lines: int = 10):
    with open('discord.log','r',encoding='utf-8') as f:
        log_lines = f.readlines()[-lines:]
    await send_long(ctx, "".join(log_lines))

@bot.command(help=" Who are you? Who owns the bot?")
async def whoami(ctx):
    owner_mentions = []
    for owner_id in OWNER_IDS:
        owner = ctx.guild.get_member(owner_id) or await bot.fetch_user(owner_id)
        owner_mentions.append(owner.mention if owner else f"User ID {owner_id}")
    await ctx.send(f" You are {ctx.author.mention}. The bot is owned by: {', '.join(owner_mentions)} </3")

@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = (datetime.now(), reason)
    await ctx.send(f"{ctx.author.mention} is now AFK: {reason}")

@bot.command(help="Shows stats of the server")
async def stats(ctx):
    embed = discord.Embed(title="Server Stats", color=0x2b2d31)
    embed.add_field(name="Users", value=ctx.guild.member_count, inline=False)
    embed.add_field(name="Channels", value=len(ctx.guild.channels), inline=False)
    await ctx.send(embed=embed)

@bot.command(help="Shows the bots permissions")
async def permissions(ctx):
    perms = ctx.channel.permissions_for(ctx.guild.me)
    perm_list = [perm for perm, value in perms if value]
    embed = discord.Embed(title="Sublimes permissions", description="\n".join(perm_list), color=0x2b2d31)
    await ctx.send(embed=embed)

@bot.command(help="Make a role")
@is_owner()
async def makerole(ctx, name: str):
    role = await ctx.guild.create_role(name=name)
    await ctx.send(f"Role created: {role.mention}")
    

@bot.command(help="Deletes a number of bot messages")
async def bclear(ctx, amount: int):
    async for message in ctx.channel.history(limit=amount + 1):
        if message.author == bot.user:
            await message.delete()
    after = await ctx.send(f"Deleted {amount} bot messages. This message will self-destruct in 3 seconds.")
    await asyncio.sleep(3)
    await after.delete()
    await ctx.message.delete()

@bot.command(help="Silent Ping")
async def sping(ctx, member: discord.Member):
    await ctx.send(f"{member.mention}", delete_after=0)
    
@bot.command(help="Shows the bot's invite link")
async def invite(ctx):
    await ctx.send("Invite me to your server: https://discord.com/oauth2/authorize?client_id=1487450682545148035&permissions=5067933499915510&integration_type=0&scope=bot - Nashatra </3")

@bot.command(help="Toggle ai")
@is_owner()
async def ai(ctx):
    global ai_enabled
    ai_enabled = not ai_enabled
    status = "enabled" if ai_enabled else "disabled"
    await ctx.send(f"AI has been {status}.")

@bot.command(help="Shows AFK users")
async def safk(ctx):
    if not afk_users:
        await ctx.send("No users are currently AFK.")
        return

    embed = discord.Embed(title="AFK Users", color=0x2b2d31)
    for user_id, (timestamp, reason) in afk_users.items():
        user = ctx.guild.get_member(user_id) or await bot.fetch_user(user_id)
        embed.add_field(name=user.name, value=f"Reason: {reason}\nTime: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}", inline=False)
    await ctx.send(embed=embed)

@bot.command(help="Github repisitory")
async def github(ctx):
    await ctx.send("Check out the source code on GitHub: https://github.com/Nashatra-dev/Sublime - Nashatra </3")    

bot.launch_time = datetime.now()
bot.run(token, log_handler=handler, log_level=logging.DEBUG)