# Goldscale

Goldscale is a Discord.py bot for deterministic D&D 5e magic item pricing.

It prices from explicit magic item inputs: rarity, item type, and what the magic item changes. It does not use item databases, infer hidden mechanics from item names, use supplied price overrides, or price mundane equipment.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a local `.env` file:

```text
DISCORD_TOKEN=your_token_here
```

Never commit `.env` or a Discord token.

## Commands

```text
?gs help
?gs buy wand of fireballs rare wand 8d6 aoe 7 charges
?gs buy potion of healing common potion 2d4+2 healing
?gs buy cloak of protection uncommon cloak +1
?gs buy +1 shield uncommon shield
?gs sell qty 2 +1 sword uncommon weapon
?formula
```

Sell mode defaults to 50%. To use a different sell rate, include a percent sign. Bare numbers are not treated as sell percentages.

## Formula Boundaries

Goldscale supports these rarity bands:

```text
common
uncommon
rare
very rare
```

Goldscale accepts item type words such as:

```text
wand, staff, potion, scroll, ammunition
weapon, armor, shield, sword, bow, dagger, axe, mace, spear
ring, cloak, boots, amulet, belt, bracers, gloves, gauntlets, helm, hat, goggles, bag, jug, robe, wondrous item
charged item, multi-use item, multi-ability item
```

Goldscale supports these magic-item effect inputs:

```text
+1/+2/+3 item bonus
damage dice, such as 8d6
healing dice, such as 2d4+2 healing
utility strength: minor, reusable, or broad
```

Utility impact is limited to:

```text
minor = 4
reusable = 6
broad = 8
```

Randomized or table-driven items must ask for explicit utility strength. Recharge dice are not damage. Supplied price overrides are rejected.

## Tests

```powershell
python -m pytest
```

## Troubleshooting

If Goldscale sends repeated identical replies, multiple bot processes are probably running.
Stop the extra Python processes, then start one fresh bot:

```powershell
Get-Process python
Get-Process python | Stop-Process
cd C:\Users\vhmfa\goldscale
python goldscale_bot.py
```
