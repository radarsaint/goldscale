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


def test_real_table_wand_of_fireballs_buy_output():
    output = render_gs("?gs buy wand of fireballs, rare complex, 8d6 aoe, 7 charges")

    assert "**Item:** Wand of Fireballs" in output
    assert "Impact: 8d6 AoE ×4 × 7 charges" in output
    assert "8d6 average = 28; AoE ×4; charges ×7; 28 × 4 × 7 = 784" in output
    assert "**Final Price**\n**157,000 gp**" in output


def test_real_table_potion_of_healing_buy_output():
    output = render_gs("?gs buy potion of healing, common consumable, 2d4+2 healing")

    assert "**Item:** Potion of Healing" in output
    assert "Impact: 2d4+2 healing" in output
    assert "2d4+2 average = 7 impact" in output
    assert "**Final Price**\n**70 gp**" in output


def test_real_table_sell_output_preserves_percent_warning_rule():
    output = render_gs("?gs sell +1 sword uncommon weapon at 75")

    assert "**Sell Rate**\n50%" in output
    assert "**Sell Price**\n**600 gp**" in output
    assert "**Warnings**" in output
    assert '• I found "75" but not "75%." For sell rates, include the percent sign.' in output


def test_real_table_randomized_item_asks_for_explicit_impact():
    output = render_gs(
        """?gs buy Wand of Wonder
Wand, rare
Description
This wand has 7 charges. Roll on the effects table."""
    )

    assert "I found **Wand of Wonder**, but I cannot price it yet." in output
    assert "• Impact: choose one pricing input" in output
    assert "Note: randomized effects detected" in output
    assert "Goldscale found randomized/table-driven effect text" in output
    assert "?gs buy Wand of Wonder, rare complex, broad utility, 7 charges" in output
