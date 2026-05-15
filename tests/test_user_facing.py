from goldscale.formatting import format_missing, format_result
from goldscale.parser import parse_item_text
from goldscale.pricing import calculate_price


def render_gs(description: str) -> str:
    data = parse_item_text(description)

    try:
        return format_result(calculate_price(data))
    except ValueError as error:
        if str(error) == "missing fields":
            return format_missing(data)
        raise


def test_loose_wand_of_fireballs_prices_successfully():
    output = render_gs("?gs buy wand of fireballs rare complex 8d6 aoe 7 charges")

    assert "**Item:** Wand of Fireballs" in output
    assert "Rarity: Rare" in output
    assert "Category: Complex" in output
    assert "Impact: 8d6 AoE ×4 × 7 charges" in output
    assert "8d6 average = 28; AoE ×4; charges ×7; 28 × 4 × 7 = 784" in output
    assert "**Final Price**\n**157,000 gp**" in output


def test_sell_defaults_to_half_price():
    output = render_gs("?gs sell +1 sword uncommon weapon")

    assert "**List Price**\n1,200 gp" in output
    assert "**Sell Rate**\n50%" in output
    assert "**Sell Price**\n**600 gp**" in output


def test_sell_custom_percent_prices_successfully():
    output = render_gs("?gs sell +1 sword uncommon weapon at 75%")

    assert "**List Price**\n1,200 gp" in output
    assert "**Sell Rate**\n75%" in output
    assert "**Sell Price**\n**900 gp**" in output


def test_sell_bare_number_blocks_instead_of_pricing():
    output = render_gs("?gs sell +1 sword uncommon weapon at 75")

    assert "**Sell Price**" not in output
    assert "I need the sell rate with a percent sign." in output
    assert 'I found "75" but not "75%."' in output
    assert "?gs sell +1 sword uncommon weapon at 75%" in output


def test_wand_of_wonder_avrae_paste_asks_for_explicit_utility_impact():
    output = render_gs(
        """?gs buy Wand of Wonder
Wand, rare
Description
This wand has 7 charges. Roll on the effects table."""
    )

    assert "**Final Price**" not in output
    assert "I found **Wand of Wonder**, but I cannot price it yet." in output
    assert "Rarity: Rare" in output
    assert 'Category: Complex (inferred from "wand")' in output
    assert "Charges: 7" in output
    assert "randomized/table-driven effects need an explicit impact" in output
    assert "?gs buy Wand of Wonder, rare complex, minor utility, 7 charges" in output
    assert "?gs buy Wand of Wonder, rare complex, reusable utility, 7 charges" in output
    assert "?gs buy Wand of Wonder, rare complex, broad utility, 7 charges" in output
    assert "8d6" not in output


def test_staff_of_power_avrae_paste_does_not_price_from_bonus_alone():
    output = render_gs(
        """?gs buy Staff of Power
Staff, very rare
Description
This staff can be wielded as a magic quarterstaff that grants a +2 bonus. It has 20 charges and several spells."""
    )

    assert "**Final Price**" not in output
    assert "I found **Staff of Power**, but I cannot price it yet." in output
    assert "Rarity: Very Rare" in output
    assert 'Category: Complex (inferred from "staff")' in output
    assert "Charges: 20" in output
    assert "Found: +2 bonus" in output
    assert "charged complex items may have additional priced effects" in output
    assert "I need an explicit impact basis." in output


def test_potion_of_healing_prices_successfully_without_commas():
    output = render_gs("?gs buy potion of healing common consumable 2d4+2 healing")

    assert "**Item:** Potion of Healing" in output
    assert "Impact: 2d4+2 healing" in output
    assert "2d4+2 average = 7 impact" in output
    assert "**Final Price**\n**70 gp**" in output


def test_missing_rarity_asks_only_for_rarity_and_preserves_known_inputs():
    output = render_gs("?gs buy +1 sword weapon")

    assert "**Final Price**" not in output
    assert "I need:" in output
    assert "Rarity: common, uncommon, rare, or very rare" in output
    assert "Category:" not in output.split("**Missing**", 1)[1].split("**Read so far**", 1)[0]
    assert "Impact:" not in output.split("**Missing**", 1)[1].split("**Read so far**", 1)[0]
    assert "?gs buy +1 Sword, rare weapon / armor, +1" in output


def test_unsupported_rarity_does_not_suggest_price():
    output = render_gs("?gs buy legendary crown broad utility")

    assert "**Final Price**" not in output
    assert "legendary is outside this formula" in output
    assert "made-up price" not in output.lower()
