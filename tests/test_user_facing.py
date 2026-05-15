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
    assert "Sell Rate: Missing or invalid" in output
    assert "?gs sell +1 sword uncommon weapon at 75%" in output


def test_invalid_sell_percent_blocks_with_range_error():
    zero = render_gs("?gs sell +1 sword uncommon weapon at 0%")
    high = render_gs("?gs sell +1 sword uncommon weapon at 125%")

    for output in (zero, high):
        assert "**Sell Price**" not in output
        assert "Sell rate must be between 1% and 100%." in output
        assert "Use a value from 1% to 100%, e.g. at 75%." in output
        assert "percent sign" not in output
        assert "Sell Rate: Missing or invalid" in output


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


def test_quantity_adds_buy_transaction_total():
    output = render_gs("?gs buy qty 3 potion of healing common consumable 2d4+2 healing")

    assert "**Item:** Potion of Healing" in output
    assert "Quantity: 3" in output
    assert "**Final Price**\n**70 gp**" in output
    assert "**Quantity**\n3" in output
    assert "**Transaction Total**\n**210 gp**" in output


def test_quantity_with_sell_adds_transaction_total():
    output = render_gs("?gs sell +1 sword uncommon weapon qty 2")

    assert "**Item:** +1 Sword" in output
    assert "Quantity: 2" in output
    assert "**List Price**\n1,200 gp" in output
    assert "**Sell Rate**\n50%" in output
    assert "**Unit Sell Price**\n**600 gp**" in output
    assert "**Quantity**\n2" in output
    assert "**Total Sell Price**\n**1,200 gp**" in output
    assert "44,000 gp" not in output


def test_prefix_quantity_with_sell_adds_correct_transaction_total():
    output = render_gs("?gs sell qty 2 +1 sword uncommon weapon")

    assert "**Item:** +1 Sword" in output
    assert "**List Price**\n1,200 gp" in output
    assert "**Sell Rate**\n50%" in output
    assert "**Unit Sell Price**\n**600 gp**" in output
    assert "**Quantity**\n2" in output
    assert "**Total Sell Price**\n**1,200 gp**" in output
    assert "44,000 gp" not in output


def test_quantity_on_weird_utility_item_adds_transaction_total():
    output = render_gs("?gs buy alchemy jug uncommon utility reusable utility qty 2")

    assert "**Item:** Alchemy Jug" in output
    assert "Quantity: 2" in output
    assert "Reusable utility = 6 impact" in output
    assert "**Final Price**\n**350 gp**" in output
    assert "**Transaction Total**\n**700 gp**" in output


def test_quantity_on_wand_of_wonder_requires_explicit_impact():
    output = render_gs("?gs buy wand of wonder rare complex qty 4")

    assert "**Final Price**" not in output
    assert "**Item:**" not in output
    assert "I found **Wand of Wonder**" in output
    assert "Quantity: 4" in output
    assert "Impact:" in output


def test_quantity_on_wand_of_wonder_with_explicit_impact_adds_transaction_total():
    output = render_gs("?gs buy wand of wonder rare complex broad 7 charges count 4")

    assert "**Item:** Wand of Wonder" in output
    assert "Charges: 7" in output
    assert "Quantity: 4" in output
    assert "Broad utility = 8 impact; charges" in output
    assert "**Final Price**\n**11,000 gp**" in output
    assert "**Transaction Total**\n**44,000 gp**" in output


def test_quantity_with_official_price_adds_exact_transaction_total():
    output = render_gs("?gs buy qty 3 named item official price 1234 gp")

    assert "**Item:** Named Item" in output
    assert "**Final Price**\n**1,234 gp**" in output
    assert "**Quantity**\n3" in output
    assert "**Transaction Total**\n**3,702 gp**" in output


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
    assert "If the DM intentionally reclassifies it" in output
    assert "?gs buy" not in output.split("**Use one**", 1)[-1]
    assert "made-up price" not in output.lower()


def test_official_price_override_wins_even_with_unsupported_rarity():
    output = render_gs("?gs buy legendary crown, official price 50000 gp")

    assert "**Item:** Legendary Crown" in output
    assert "Official price override used." in output
    assert "Official price override ignores rarity/category formula limits." in output
    assert "**Final Price**\n**50,000 gp**" in output
    assert "outside this formula" not in output


def test_flattened_avrae_paste_drops_generic_speaker_text():
    output = render_gs(
        "?gs buy Table User Wand of Wonder Wand, rare Description This wand has 7 charges. Roll on the effects table."
    )

    assert "I found **Wand of Wonder**, but I cannot price it yet." in output
    assert 'Category: Complex (inferred from "wand")' in output
    assert "Charges: 7" in output


def test_help_mentions_manual_spell_dice_requirement():
    from goldscale.formatting import help_text

    output = help_text()

    assert output.startswith("**Goldscale Help**\n\n```text\n?gs buy +1 sword uncommon weapon")
    assert "If a pasted item description names a spell but does not include damage/healing dice, add the dice manually." in output
    assert "Goldscale will not invent utility tiers, official prices, or hidden item mechanics." in output
    assert "Custom sell rates need a percent sign, e.g. `at 75%`." in output
