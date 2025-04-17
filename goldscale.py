import discord
from discord.ext import commands
import os
TOKEN = os.getenv("GOLDSCALE_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🟢 Goldscale is online as {bot.user}!")

@bot.command()
async def ping(ctx):
    await ctx.send("Goldscale hears the clink of your coin.")

bot.run(TOKEN)
