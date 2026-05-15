import pytest

from goldscale.parser import parse_item_text
from goldscale.pricing import missing_fields


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
    assert data.quantity is None


def test_parses_explicit_quantity_without_using_bare_numbers():
    explicit = parse_item_text("?gs buy potion of healing common consumable 2d4+2 healing qty 3")
    prefix = parse_item_text("?gs buy qty 3 potion of healing common consumable 2d4+2 healing")
    bare = parse_item_text("?gs buy potion of healing common consumable 2d4+2 healing 3")

    assert explicit.quantity == 3
    assert prefix.quantity == 3
    assert prefix.item_name == "Potion of Healing"
    assert bare.quantity is None


@pytest.mark.parametrize(
    ("command", "quantity"),
    [
        ("?gs buy potion of healing common consumable 2d4+2 healing quantity 1", 1),
        ("?gs buy spell scroll common consumable 1d6 damage qty 2", 2),
        ("?gs buy +1 sword uncommon weapon count 4", 4),
        ("?gs buy useful cloak uncommon utility reusable utility quantity 12", 12),
        ("?gs buy wand of sparks rare complex 8d6 qty 25", 25),
    ],
)
def test_parses_quantity_keywords_across_item_inputs(command, quantity):
    data = parse_item_text(command)

    assert data.quantity == quantity


def test_quantity_does_not_confuse_bonus_charges_or_sell_percent():
    bonus = parse_item_text("?gs buy +1 sword uncommon weapon")
    charged = parse_item_text("?gs buy wand of fireballs, rare complex, 8d6 aoe, 7 charges")
    sell = parse_item_text("?gs sell +1 sword uncommon weapon at 75%")
    official = parse_item_text("?gs buy named item, official price 1200 gp")

    assert bonus.quantity is None
    assert charged.quantity is None
    assert sell.quantity is None
    assert official.quantity is None


def test_quantity_keyword_does_not_override_charges():
    data = parse_item_text("?gs buy wand of sparks, rare complex, 8d6, 7 charges, qty 3")

    assert data.charges == 7
    assert data.quantity == 3


@pytest.mark.parametrize(
    ("command", "quantity"),
    [
        ("?gs buy alchemy jug uncommon utility reusable utility qty 2", 2),
        ("?gs buy boots of the winding path uncommon utility reusable utility quantity 3", 3),
        ("?gs buy wand of wonder rare complex broad 7 charges count 4", 4),
        ("?gs buy immovable rod uncommon utility reusable utility qty 5", 5),
        ("?gs buy bag of holding uncommon utility broad utility quantity 6", 6),
        ("?gs buy deck of illusions uncommon complex broad utility qty 7", 7),
    ],
)
def test_quantity_on_weird_items_uses_explicit_inputs_only(command, quantity):
    data = parse_item_text(command)

    assert data.quantity == quantity
    assert data.utility in {"reusable", "broad"}


def test_weird_item_name_alone_still_does_not_supply_impact():
    data = parse_item_text("?gs buy alchemy jug uncommon utility qty 2")

    assert data.item_name == "Alchemy Jug"
    assert data.quantity == 2
    assert data.utility is None
    assert "Impact:" in missing_fields(data)[0]


def test_recharge_dice_are_not_damage():
    data = parse_item_text(
        "?gs buy steady wand, rare complex. The wand regains 1d6 + 1 expended charges daily at dawn."
    )

    assert data.damage is None
    assert data.healing is None
    assert data.charges is None


def test_srd_style_last_charge_d20_is_not_damage():
    data = parse_item_text(
        "?gs buy fragile wand, uncommon wand. This wand has 7 charges. If you expend the last charge, roll a d20. On a 1, the wand is destroyed."
    )

    assert data.damage is None
    assert data.healing is None
    assert data.charges == 7


def test_randomized_table_driven_items_require_explicit_impact():
    data = parse_item_text("?gs buy wand of wonder, rare wand. Roll on the effects table.")

    assert data.randomized is True
    assert data.category == "complex"
    assert missing_fields(data) == [
        "Impact: choose a utility tier: minor utility, reusable utility, or broad utility"
    ]


def test_save_dc_and_range_are_not_impact_or_aoe():
    data = parse_item_text(
        "?gs buy control wand, rare wand. This wand has 7 charges. Choose one creature you can see within 120 feet. The target must make a DC 15 Wisdom saving throw."
    )

    assert data.damage is None
    assert data.healing is None
    assert data.bonus is None
    assert data.aoe is False
    assert data.charges == 7


def test_point_of_origin_alone_is_not_aoe():
    data = parse_item_text(
        "?gs buy point wand, rare wand. Choose a point of origin within 120 feet of you."
    )

    assert data.aoe is False


def test_quantity_dice_are_not_damage():
    data = parse_item_text("?gs buy bead necklace, rare consumable, 1d6 + 3 beads")

    assert data.damage is None
    assert data.healing is None


def test_explicit_area_shape_still_sets_aoe():
    data = parse_item_text("?gs buy blast wand, rare complex, 8d6 damage in a 20-foot radius")

    assert data.damage == "8d6"
    assert data.aoe is True


def test_charged_complex_bonus_still_needs_explicit_impact_basis():
    data = parse_item_text(
        "?gs buy power staff, very rare staff. You gain a +1 bonus while holding it. This staff has 20 charges."
    )

    assert data.bonus == 1
    assert data.charges == 20
    assert data.complex_partial_bonus is True


def test_sell_percent_requires_percent_sign():
    data = parse_item_text("?gs sell +1 sword uncommon weapon at 75%")

    assert data.mode == "sell"
    assert data.sell_rate == pytest.approx(0.75)
    assert data.warnings == []


def test_bare_sell_number_is_warning_not_sell_rate():
    data = parse_item_text("?gs sell +1 sword uncommon weapon at 75")

    assert data.mode == "sell"
    assert data.sell_rate is None
    assert data.sell_rate_error == "I need the sell rate with a percent sign."
    assert data.sell_rate_retry_command == "?gs sell +1 sword uncommon weapon at 75%"
    assert data.warnings == ['I found "75" but not "75%." For sell rates, include the percent sign.']
    assert missing_fields(data)[0] == "Sell rate: include the percent sign"
