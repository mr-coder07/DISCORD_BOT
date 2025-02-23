import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from cogs.crypto import Crypto
from cogs.competition import Competition


import asyncio
import discord  # Assuming you need the discord library imported here

# Set the Windows event loop policy if running on Windows
if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# Load environment variables from .env file
load_dotenv()

# Load token from environment variable
TOKEN = os.getenv("DISCORD_TOKEN")

# Define intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Remove the default help command
bot.remove_command('help')

# Load the cogs on bot ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Setup hook for adding cogs
async def setup_hook():
    await bot.add_cog(Crypto(bot))  # Add the Crypto cog
    await bot.add_cog(Competition(bot))  # Add the Competition cog

bot.setup_hook = setup_hook  # Set the bot's setup hook

# Run the bot
bot.run(TOKEN)
