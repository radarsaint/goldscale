import pytest

from goldscale.parser import ItemData, parse_item_text
from goldscale.pricing import average_dice, calculate_price, clean_shop_value


def test_average_dice_math():
    assert average_dice("8d6") == pytest.approx(28)
    assert average_dice("2d4+2") == pytest.approx(7)


def test_clean_shop_rounding():
    assert clean_shop_value(27) == 25
    assert clean_shop_value(112) == 100
    assert clean_shop_value(1660) == 1700
    assert clean_shop_value(10240) == 10000


def test_bonus_pricing():
    result = calculate_price(parse_item_text("?gs buy +1 sword uncommon weapon"))

    assert result.impact == 24
    assert result.gpi == 50
    assert result.final_price == 1200


def test_damage_pricing():
    result = calculate_price(parse_item_text("?gs buy wand of sparks, rare complex, 8d6"))

    assert result.impact == pytest.approx(28)
    assert result.gpi == 200
    assert result.final_price == 5600


def test_aoe_and_charges_multiplier():
    result = calculate_price(parse_item_text("?gs buy wand of fireballs, rare complex, 8d6 aoe, 7 charges"))

    assert result.impact == pytest.approx(28 * 4 * 7)
    assert result.final_price == 157000


def test_utility_tiers_only():
    minor = calculate_price(parse_item_text("?gs buy cloak one, uncommon utility, minor utility"))
    reusable = calculate_price(parse_item_text("?gs buy cloak two, uncommon utility, reusable utility"))
    broad = calculate_price(parse_item_text("?gs buy cloak three, uncommon utility, broad utility"))
    invalid = ItemData(item_name="Cloak Four", rarity="uncommon", category="utility", utility="strong")

    assert minor.impact == 4
    assert reusable.impact == 6
    assert broad.impact == 8
    with pytest.raises(KeyError):
        calculate_price(invalid)


def test_official_price_override_only_when_explicitly_supplied():
    # 1234 gp is an arbitrary sentinel proving official price overrides are not rounded; it is not item data.
    explicit = calculate_price(parse_item_text("?gs buy named item, official price 1234 gp"))
    bare = parse_item_text("?gs buy named item, 1234 gp")

    assert explicit.list_price == 1234
    assert explicit.final_price == 1234
    assert bare.official_price is None
