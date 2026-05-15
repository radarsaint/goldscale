import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from goldscale.formatting import format_missing, format_result, formula_text, help_text
from goldscale.parser import parse_item_text
from goldscale.pricing import calculate_price


COMMAND_PREFIX = "?"


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=intents,
    help_command=None,
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command(name="formula")
async def formula_command(ctx):
    await ctx.reply(formula_text())


@bot.command(name="gs")
async def gs_command(ctx, *, description: str = ""):
    if not description.strip() or description.strip().lower() == "help":
        await ctx.reply(help_text())
        return

    data = parse_item_text(description)

    try:
        result = calculate_price(data)
        await ctx.reply(format_result(result))
    except ValueError as error:
        if str(error) == "missing fields":
            await ctx.reply(format_missing(data))
        else:
            await ctx.reply(f"Could not price item: {error}")


def run_bot() -> None:
    bot.run(TOKEN)

