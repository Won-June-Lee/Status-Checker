import discord
from discord.ext import commands
import json
import os
import webserver

DISCORD_TOKEN = os.environ['discordkey']

# Define the bot's prefix and intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Database file
db_file = 'games_db.json'

# Load the database
def load_db():
    if not os.path.exists(db_file):
        return {}
    with open(db_file, 'r') as f:
        return json.load(f)

# Save the database
def save_db(data):
    with open(db_file, 'w') as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Bot is ready!')

# --- Existing Commands (No changes needed) ---

# Command to add a game to a user's profile
@bot.command(name='addgame')
async def add_game(ctx, *, game_name: str):
    """Adds a game to your list of played games."""
    user_id = str(ctx.author.id)
    db = load_db()

    if user_id not in db:
        db[user_id] = []

    if game_name.lower() in [g.lower() for g in db[user_id]]:
        await ctx.send(f'**{game_name}** is already in your list!')
        return

    db[user_id].append(game_name)
    save_db(db)
    await ctx.send(f'Added **{game_name}** to your games list!')

# Command to remove a game from a user's profile
@bot.command(name='removegame')
async def remove_game(ctx, *, game_name: str):
    """Removes a game from your list of played games."""
    user_id = str(ctx.author.id)
    db = load_db()

    if user_id not in db or game_name not in db[user_id]:
        await ctx.send(f'**{game_name}** is not in your list.')
        return

    db[user_id].remove(game_name)
    save_db(db)
    await ctx.send(f'Removed **{game_name}** from your games list!')

# Command to view a user's profile
@bot.command(name='profile')
async def view_profile(ctx, member: discord.Member = None):
    """Displays a user's games list."""
    if member is None:
        member = ctx.author

    user_id = str(member.id)
    db = load_db()

    if user_id not in db or not db[user_id]:
        await ctx.send(f'**{member.display_name}** has not added any games yet.')
        return

    games_list = '\n'.join(f'- {game}' for game in db[user_id])
    embed = discord.Embed(
        title=f"{member.display_name}'s Game History",
        description=games_list,
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url)
    await ctx.send(embed=embed)

# --- New Bulk Commands ---

@bot.command(name='bulkadd')
@commands.has_permissions(manage_messages=True) # Require a permission, e.g., "Manage Messages"
async def bulk_add_games(ctx, members: commands.Greedy[discord.Member], *, game_name: str):
    """Adds a game to multiple users' profiles.
    Usage: !bulkadd @user1 @user2 "Game Name"
    """
    db = load_db()
    
    added_to = []
    already_had = []
    
    print(game_name)

    for member in members:
        user_id = str(member.id)
        if user_id not in db:
            db[user_id] = []
            
        if game_name.lower() in [g.lower() for g in db[user_id]]:
            already_had.append(member.display_name)
        else:
            db[user_id].append(game_name)
            added_to.append(member.display_name)
    
    save_db(db)
    
    response = f"**Games updated for {len(added_to) + len(already_had)} members:**\n"
    
    if added_to:
        added_list = ", ".join(added_to)
        response += f"✅ Added **{game_name}** to: {added_list}\n"
    
    if already_had:
        had_list = ", ".join(already_had)
        response += f"⚠️ **{game_name}** was already in the list for: {had_list}"
        
    await ctx.send(response)

@bot.command(name='bulkremove')
@commands.has_permissions(manage_messages=True)
async def bulk_remove_games(ctx, members: commands.Greedy[discord.Member], *, game_name: str):
    """Removes a game from multiple users' profiles.
    Usage: !bulkremove @user1 @user2 "Game Name"
    """
    db = load_db()
    
    removed_from = []
    did_not_have = []
    
    for member in members:
        user_id = str(member.id)
        
        if user_id in db and game_name in db[user_id]:
            db[user_id].remove(game_name)
            removed_from.append(member.display_name)
        else:
            did_not_have.append(member.display_name)
            
    save_db(db)
    
    response = f"**Games updated for {len(removed_from) + len(did_not_have)} members:**\n"
    
    if removed_from:
        removed_list = ", ".join(removed_from)
        response += f"✅ Removed **{game_name}** from: {removed_list}\n"
        
    if did_not_have:
        did_not_have_list = ", ".join(did_not_have)
        response += f"⚠️ **{game_name}** was not found for: {did_not_have_list}"
        
    await ctx.send(response)

webserver.keep_alive()
# Run the bot with your token
bot.run(DISCORD_TOKEN)