from goldscale.parser import ItemData
from goldscale.pricing import PricingResult, has_impact, missing_fields


def item_type_retry_text(data: ItemData) -> str:
    if data.category_source and data.category_source.startswith('inferred from "'):
        return data.category_source.split('"', 2)[1]

    if data.category == "consumable":
        return "potion"

    if data.category == "weapon / armor":
        return "weapon"

    if data.category == "utility":
        return "cloak"

    if data.category == "complex":
        return "wand"

    if data.bonus is not None:
        return "weapon"

    return "wand"


def impact_retry_text(data: ItemData) -> str:
    if data.bonus is not None:
        return f"+{data.bonus}"

    if data.damage is not None:
        return data.damage

    if data.healing is not None:
        return f"{data.healing} healing"

    if data.utility is not None:
        return f"{data.utility} utility"

    return "impact here"


def build_retry_example(data: ItemData) -> str:
    mode = data.mode or "buy"
    name = data.item_name or "item name"
    rarity = data.rarity or "uncommon"
    item_type = item_type_retry_text(data)
    impact = impact_retry_text(data)

    parts = [f"?gs {mode} {name}", f"{rarity} {item_type}", impact]

    if data.aoe and "utility" not in impact and impact != "impact here":
        parts.append("aoe")

    if data.charges:
        parts.append(f"{data.charges} charges")
    elif data.category == "complex" and impact != "impact here":
        parts.append("7 charges")

    command = ", ".join(parts)

    if mode == "sell" and data.sell_rate and data.sell_rate != 0.50:
        command += f" at {int(data.sell_rate * 100)}%"
    elif mode == "sell" and data.sell_rate_retry:
        command += f" at {data.sell_rate_retry}%"

    return command


def build_retry_options(data: ItemData) -> str:
    mode = data.mode or "buy"
    name = data.item_name or "item name"
    rarity = data.rarity or "rare"
    item_type = item_type_retry_text(data)

    suffix = f", {data.charges} charges" if data.charges else ""

    if data.sell_rate_error:
        if data.sell_rate_retry_command:
            return data.sell_rate_retry_command
        return build_retry_example(data)

    if data.unsupported_rarity:
        return "If the DM intentionally reclassifies it, choose common, uncommon, rare, or very rare and run the command again."

    if not has_impact(data):
        options = [
            f"?gs {mode} {name}, {rarity} {item_type}, minor utility{suffix}",
            f"?gs {mode} {name}, {rarity} {item_type}, reusable utility{suffix}",
            f"?gs {mode} {name}, {rarity} {item_type}, broad utility{suffix}",
        ]

        if not data.randomized and not data.complex_partial_bonus:
            options.append(f"?gs {mode} {name}, {rarity} {item_type}, 8d6 aoe{suffix}")

        return "\n".join(options)

    return build_retry_example(data)


def read_as_block(data: ItemData, player_language: bool = False) -> str:
    pieces = [
        f"Item: {data.item_name or 'Missing'}",
        f"Mode: {data.mode.title()}",
    ]

    if data.unsupported_rarity:
        pieces.append(f"Rarity: {data.unsupported_rarity.title()} (unsupported)")
    else:
        pieces.append(f"Rarity: {data.rarity.title() if data.rarity else 'Missing'}")

    if data.category:
        source = f" ({data.category_source})" if data.category_source else ""
        label = "Item Type" if player_language else "Category"
        pieces.append(f"{label}: {data.category.title()}{source}")
    else:
        label = "Item Type" if player_language else "Category"
        pieces.append(f"{label}: Missing")

    if data.charges:
        pieces.append(f"Charges: {data.charges}")

    if data.quantity:
        pieces.append(f"Quantity: {data.quantity}")

    if data.complex_partial_bonus:
        pieces.append(f"Found: +{data.bonus} bonus")
        pieces.append(("What It Changes" if player_language else "Impact") + ": Missing")
        pieces.append("Note: charged complex item has additional abilities")
    elif data.bonus is not None:
        pieces.append(f"{'What It Changes' if player_language else 'Impact'}: +{data.bonus} bonus")
    elif data.damage is not None:
        impact = f"{'What It Changes' if player_language else 'Impact'}: {data.damage}"
        if data.aoe:
            impact += " AoE ×4"
        if data.charges:
            impact += f" × {data.charges} charges"
        pieces.append(impact)
    elif data.healing is not None:
        impact = f"{'What It Changes' if player_language else 'Impact'}: {data.healing} healing"
        if data.aoe:
            impact += " AoE ×4"
        if data.charges:
            impact += f" × {data.charges} charges"
        pieces.append(impact)
    elif data.utility is not None:
        impact = f"{'Utility Strength' if player_language else 'Impact'}: {data.utility.title()} utility"
        if data.charges:
            impact += f" × {data.charges} charges"
        pieces.append(impact)
    else:
        pieces.append(("What It Changes" if player_language else "Impact") + ": Missing")

    if data.randomized and not has_impact(data):
        pieces.append("Note: randomized effects detected")

    if data.mode == "sell":
        if data.sell_rate_error:
            pieces.append("Sell Rate: Missing or invalid")
        else:
            pieces.append(f"Sell Rate: {int((data.sell_rate or 0.50) * 100)}%")

    return "\n".join(pieces)


def format_missing(data: ItemData) -> str:
    if data.rejection_error:
        return data.rejection_error

    missing = missing_fields(data)
    retry_options = build_retry_options(data)

    need_text = "I need:"
    extra_note = ""
    if data.sell_rate_error:
        extra_note = "\n\n" + data.sell_rate_error
        if data.sell_rate_error == "Sell rate must be between 1% and 100%.":
            extra_note += " Use a value from 1% to 100%, e.g. at 75%."
        if data.warnings and data.warnings[0] != data.sell_rate_error:
            extra_note += " " + " ".join(data.warnings)
    elif data.unsupported_rarity:
        extra_note = "\n\nIf the DM intentionally reclassifies it, choose common, uncommon, rare, or very rare and run the command again."
    elif data.complex_partial_bonus and not has_impact(data):
        need_text = "I need what the magic item changes."
        extra_note = "\n\nGoldscale found a +bonus, but charged items may have additional priced effects. It will not treat the +bonus alone as the whole item unless you explicitly price it that way."
    elif data.randomized and not has_impact(data):
        extra_note = "\n\nGoldscale found randomized/table-driven effects need a utility strength. It will not price this until you choose minor, reusable, or broad."

    return f"""
I found **{data.item_name or "that item"}**, but I cannot price it yet.

**Missing**
{need_text}
{chr(10).join(f"• {item}" for item in missing)}{extra_note}

**Read so far**
```text
{read_as_block(data, player_language=True)}
```

**Use one**
```text
{retry_options}
```
""".strip()


def format_result(result: PricingResult) -> str:
    warnings = ""
    if result.warnings:
        warnings = "\n\n**Warnings**\n" + "\n".join(f"• {warning}" for warning in result.warnings)

    if result.mode == "sell":
        sell_price_label = "Unit Sell Price" if result.quantity else "Sell Price"
        return f"""
**Item:** {result.item_name}

**Read as**
```text
{result.read_as}
```

**Impact Calculation**
{result.impact_math}

**Rarity Band**
{result.rarity}

**Item Category**
{result.category}

**Gold Per Impact**
{result.gpi} gp

**List Price**
{result.list_price:,} gp

**Sell Rate**
{int((result.sell_rate or 0.50) * 100)}%

**{sell_price_label}**
**{result.final_price:,} gp**
{format_transaction_total(result, "Total Sell Price")}{warnings}
""".strip()

    return f"""
**Item:** {result.item_name}

**Read as**
```text
{result.read_as}
```

**Impact Calculation**
{result.impact_math}

**Rarity Band**
{result.rarity}

**Item Category**
{result.category}

**Gold Per Impact**
{result.gpi} gp

**Final Price**
**{result.final_price:,} gp**
{format_transaction_total(result, "Transaction Total")}{warnings}
""".strip()


def format_transaction_total(result: PricingResult, label: str) -> str:
    if not result.quantity or result.transaction_total is None:
        return ""

    return f"""

**Quantity**
{result.quantity}

**{label}**
**{result.transaction_total:,} gp**"""


def help_text() -> str:
    return """
**Goldscale Help**

```text
?gs buy wand of fireballs rare wand 8d6 aoe 7 charges
?gs buy potion of healing common potion 2d4+2 healing
?gs buy cloak of protection uncommon cloak +1
?gs buy ring of protection rare ring +1
?gs buy +1 shield uncommon shield
?gs buy scroll of fireball uncommon scroll 8d6 aoe
?gs buy wand of wonder rare wand broad 7 charges
?gs sell qty 2 +1 sword uncommon weapon
?formula
```

Goldscale prices from explicit inputs:
```text
rarity + item type + what the magic item changes
```

Supported rarity:
```text
common, uncommon, rare, very rare
```

Supported item type words include:
```text
wand, staff, rod, potion, scroll, ammunition, weapon, armor, shield, sword, bow, ring, cloak, boots, amulet, wondrous item, charged item
```

What the magic item changes:
```text
+1, +2, +3
8d6
2d4+2 healing
utility strength: minor, reusable, broad
```

You can paste an Avrae item description after `?gs buy`.

If a pasted item description names a spell but does not include damage/healing dice, add the dice manually.

Goldscale will not invent utility strength, supplied prices, or hidden item mechanics.

Sell defaults to 50%. Custom sell rates need a percent sign, e.g. `at 75%`.
""".strip()


def formula_text() -> str:
    return """
**Goldscale Formula**

**1. Impact**

Damage or healing:
```text
Impact = average roll
```

AoE:
```text
AoE Impact = average roll × 4
```

Weapon / armor bonus:
```text
Impact per level = bonus × 24
```

Charged item:
```text
Impact = average effect × charges
```

AoE charged item:
```text
Impact = average effect × 4 × charges
```

Utility:
```text
Minor = 4
Reusable = 6
Broad = 8
```

Charged utility:
```text
Impact = utility impact × charges
```

**2. Rarity Bands**
```text
Common: Level 1–4
Uncommon: Level 5–8
Rare: Level 9–12
Very Rare: Level 13–16
```

**3. Gold per Impact**

Common:
```text
All categories = 10 gp
```

Uncommon:
```text
Consumable 30
Weapon / Armor 50
Utility 60
Complex 80
```

Rare:
```text
Consumable 80
Weapon / Armor 120
Utility 150
Complex 200
```

Very Rare:
```text
Consumable 200
Weapon / Armor 300
Utility 400
Complex 500
```

**4. Price**
```text
Price = Impact × Gold per Impact
```

Then round to a clean shop value.
""".strip()
