import pytest

from goldscale_bot import missing_fields, parse_item_text


def test_detects_supported_and_unsupported_rarity():
    rare = parse_item_text("?gs buy wand of fireballs, rare complex, 8d6")
    legendary = parse_item_text("?gs buy impossible crown, legendary utility, broad utility")

    assert rare.rarity == "rare"
    assert rare.unsupported_rarity is None
    assert legendary.rarity is None
    assert legendary.unsupported_rarity == "legendary"
    assert missing_fields(legendary) == [
        "Rarity: legendary is outside this formula. Use common, uncommon, rare, or very rare."
    ]


def test_parses_explicit_category():
    data = parse_item_text("?gs buy useful cloak, uncommon utility, reusable")

    assert data.category == "utility"
    assert data.category_source == "explicit category"
    assert data.utility == "reusable"


def test_infers_category_from_item_type_only():
    data = parse_item_text("?gs buy plain wand, rare, 8d6")

    assert data.category == "complex"
    assert data.category_source == 'inferred from "wand"'


def test_parses_real_aoe_charged_command():
    data = parse_item_text("?gs buy wand of fireballs, rare complex, 8d6 aoe, 7 charges")

    assert data.item_name == "Wand of Fireballs"
    assert data.rarity == "rare"
    assert data.category == "complex"
    assert data.damage == "8d6"
    assert data.aoe is True
    assert data.charges == 7


def test_recharge_dice_are_not_damage():
    data = parse_item_text(
        "?gs buy steady wand, rare complex. The wand regains 1d6 + 1 expended charges daily at dawn."
    )

    assert data.damage is None
    assert data.healing is None
    assert data.charges is None


def test_randomized_table_driven_items_require_explicit_impact():
    data = parse_item_text("?gs buy wand of wonder, rare wand. Roll on the effects table.")

    assert data.randomized is True
    assert data.category == "complex"
    assert "Impact: choose one pricing input" in missing_fields(data)[0]


def test_sell_percent_requires_percent_sign():
    data = parse_item_text("?gs sell +1 sword uncommon weapon at 75%")

    assert data.mode == "sell"
    assert data.sell_rate == pytest.approx(0.75)
    assert data.warnings == []


def test_bare_sell_number_is_warning_not_sell_rate():
    data = parse_item_text("?gs sell +1 sword uncommon weapon at 75")

    assert data.mode == "sell"
    assert data.sell_rate == pytest.approx(0.50)
    assert data.warnings == ['I found "75" but not "75%." For sell rates, include the percent sign.']
