import re
from dataclasses import dataclass
from typing import Optional

from goldscale.parser import ItemData, UTILITY_IMPACT


RARITY_GPI = {
    "common": {
        "consumable": 10,
        "weapon / armor": 10,
        "utility": 10,
        "complex": 10,
    },
    "uncommon": {
        "consumable": 30,
        "weapon / armor": 50,
        "utility": 60,
        "complex": 80,
    },
    "rare": {
        "consumable": 80,
        "weapon / armor": 120,
        "utility": 150,
        "complex": 200,
    },
    "very rare": {
        "consumable": 200,
        "weapon / armor": 300,
        "utility": 400,
        "complex": 500,
    },
}


@dataclass
class PricingResult:
    item_name: str
    impact: float
    impact_math: str
    rarity: str
    category: str
    gpi: int
    list_price: int
    final_price: int
    mode: str
    sell_rate: Optional[float]
    read_as: str
    warnings: list[str]


def average_dice(expr: str) -> float:
    expr = expr.lower().replace(" ", "")
    match = re.fullmatch(r"(\d+)d(\d+)([+-]\d+)?", expr)

    if not match:
        raise ValueError("Invalid dice expression.")

    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3) or 0)

    return count * ((sides + 1) / 2) + modifier


def clean_shop_value(value: float) -> int:
    if value < 100:
        step = 5
    elif value < 1000:
        step = 25
    elif value < 10000:
        step = 100
    else:
        step = 500

    return int(round(value / step) * step)


def has_impact(data: ItemData) -> bool:
    if data.complex_partial_bonus:
        return False

    return any([
        data.bonus is not None,
        data.damage is not None,
        data.healing is not None,
        data.utility is not None,
        data.official_price is not None,
    ])


def missing_fields(data: ItemData) -> list[str]:
    missing = []

    if data.sell_rate_error:
        missing.append("Sell rate: include the percent sign")

    if data.unsupported_rarity:
        missing.append(f"Rarity: {data.unsupported_rarity} is outside this formula. Use common, uncommon, rare, or very rare.")
        return missing

    if not data.rarity and data.official_price is None:
        missing.append("Rarity: common, uncommon, rare, or very rare")

    if not data.category and data.official_price is None:
        missing.append("Category: consumable, weapon, armor, utility, or complex")

    if not has_impact(data):
        if data.complex_partial_bonus:
            missing.append("Impact: found a +bonus on a charged complex item, but that is probably not the whole item. Choose a pricing input: minor utility, reusable utility, broad utility, dice like 8d6, or provide an official price")
        elif data.randomized:
            missing.append("Impact: choose a utility tier: minor utility, reusable utility, or broad utility")
        else:
            missing.append("Impact: +1/+2/+3, dice like 8d6, healing like 2d4+2 healing, or utility tier: minor/reusable/broad")

    return missing


def calculate_price(data: ItemData) -> PricingResult:
    from goldscale.formatting import read_as_block

    missing = missing_fields(data)
    if missing:
        raise ValueError("missing fields")

    item_name = data.item_name or "Unnamed Item"

    if data.official_price is not None:
        list_price = data.official_price
        final_price = list_price

        if data.mode == "sell":
            final_price = clean_shop_value(list_price * (data.sell_rate or 0.50))

        return PricingResult(
            item_name=item_name,
            impact=0,
            impact_math="Official price override used.",
            rarity=(data.rarity or "Official").title(),
            category=(data.category or "Official").title(),
            gpi=0,
            list_price=list_price,
            final_price=final_price,
            mode=data.mode,
            sell_rate=data.sell_rate,
            read_as=read_as_block(data),
            warnings=data.warnings,
        )

    rarity = data.rarity
    category = data.category

    if rarity not in RARITY_GPI:
        raise ValueError("Rarity must be Common, Uncommon, Rare, or Very Rare.")

    if category not in RARITY_GPI[rarity]:
        raise ValueError("Category must be Consumable, Weapon, Armor, Utility, or Complex.")

    if data.bonus is not None:
        impact = data.bonus * 24
        impact_math = f"{data.bonus} × 24 = {impact} impact per level"

    elif data.damage is not None or data.healing is not None:
        expr = data.damage or data.healing
        avg = average_dice(expr)

        if data.aoe and data.charges:
            impact = avg * 4 * data.charges
            impact_math = f"{expr} average = {avg:g}; AoE ×4; charges ×{data.charges}; {avg:g} × 4 × {data.charges} = {impact:g}"
        elif data.aoe:
            impact = avg * 4
            impact_math = f"{expr} average = {avg:g}; AoE ×4; {avg:g} × 4 = {impact:g}"
        elif data.charges:
            impact = avg * data.charges
            impact_math = f"{expr} average = {avg:g}; charges ×{data.charges}; {avg:g} × {data.charges} = {impact:g}"
        else:
            impact = avg
            impact_math = f"{expr} average = {avg:g} impact"

    elif data.utility is not None:
        utility_impact = UTILITY_IMPACT[data.utility]

        if data.charges:
            impact = utility_impact * data.charges
            impact_math = f"{data.utility.title()} utility = {utility_impact} impact; charges ×{data.charges}; {utility_impact} × {data.charges} = {impact} impact"
        else:
            impact = utility_impact
            impact_math = f"{data.utility.title()} utility = {impact} impact"

    else:
        raise ValueError("Description needs +1/+2/+3, damage, healing, or a utility tier.")

    gpi = RARITY_GPI[rarity][category]
    list_price = clean_shop_value(impact * gpi)

    final_price = list_price
    if data.mode == "sell":
        final_price = clean_shop_value(list_price * (data.sell_rate or 0.50))

    return PricingResult(
        item_name=item_name,
        impact=impact,
        impact_math=impact_math,
        rarity=rarity.title(),
        category=category.title(),
        gpi=gpi,
        list_price=list_price,
        final_price=final_price,
        mode=data.mode,
        sell_rate=data.sell_rate,
        read_as=read_as_block(data),
        warnings=data.warnings,
    )
