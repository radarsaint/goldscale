import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from goldscale.clarification import (
    PendingAppraisals,
    cancel_appraisal,
    continue_appraisal,
    start_appraisal,
)
from goldscale.formatting import formula_text, help_text


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

pending_appraisals = PendingAppraisals()


def pending_key_from_message(message) -> tuple[int | None, int, int]:
    guild_id = message.guild.id if message.guild else None
    return guild_id, message.channel.id, message.author.id


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if not message.content.startswith(COMMAND_PREFIX):
        response = continue_appraisal(message.content, pending_key_from_message(message), pending_appraisals)
        if response:
            await message.reply(response)
            return

    await bot.process_commands(message)


@bot.command(name="formula")
async def formula_command(ctx):
    await ctx.reply(formula_text())


@bot.command(name="gs")
async def gs_command(ctx, *, description: str = ""):
    if not description.strip() or description.strip().lower() == "help":
        await ctx.reply(help_text())
        return

    if description.strip().lower() == "cancel":
        await ctx.reply(cancel_appraisal(pending_key_from_message(ctx.message), pending_appraisals))
        return

    await ctx.reply(start_appraisal(description, pending_key_from_message(ctx.message), pending_appraisals))


def run_bot() -> None:
    bot.run(TOKEN)
