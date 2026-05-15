# Goldscale

Goldscale is a Discord.py bot for deterministic D&D 5e magic item pricing.

It prices from explicit inputs: rarity, category, and impact. It does not use item databases, infer mechanics from item names, or invent official prices.

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
?gs buy +1 sword uncommon weapon
?gs buy wand of fireballs, rare complex, 8d6 aoe, 7 charges
?gs buy potion of healing, common consumable, 2d4+2 healing
?gs buy cloak of useful nonsense, uncommon utility, reusable
?gs sell +1 sword uncommon weapon at 75%
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

Goldscale supports these categories:

```text
consumable
weapon / armor
utility
complex
```

Goldscale supports these impact inputs:

```text
+1/+2/+3 item bonus
damage dice, such as 8d6
healing dice, such as 2d4+2 healing
utility tier: minor, reusable, or broad
explicit official price override
```

Utility impact is limited to:

```text
minor = 4
reusable = 6
broad = 8
```

Randomized or table-driven items must ask for explicit impact. Recharge dice are not damage. Official prices are only used when explicitly supplied.

## Tests

```powershell
python -m pytest
```
