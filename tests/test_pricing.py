import pytest

from goldscale.parser import ItemData, parse_item_text
from goldscale.pricing import average_dice, calculate_price, clean_shop_value, missing_fields


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


@pytest.mark.parametrize(
    "command",
    [
        "?gs buy plus 1 longsword uncommon weapon",
        "?gs buy plus one longsword uncommon weapon",
        "?gs buy plus-one longsword uncommon weapon",
        "?gs buy longsword plus one uncommon weapon",
        "?gs buy + 1 longsword uncommon weapon",
    ],
)
def test_natural_language_plus_one_longsword_prices_like_symbolic_plus_one(command):
    symbolic = calculate_price(parse_item_text("?gs buy +1 longsword uncommon weapon"))
    natural = calculate_price(parse_item_text(command))

    assert natural.impact == symbolic.impact
    assert natural.gpi == symbolic.gpi
    assert natural.final_price == symbolic.final_price


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


def test_supplied_price_override_is_rejected():
    data = parse_item_text("?gs buy named item, official price 1234 gp")

    with pytest.raises(ValueError, match="missing fields"):
        calculate_price(data)

    assert missing_fields(data) == [
        "Goldscale supplies prices from the magic item formula. It does not use supplied price overrides."
    ]


def test_quantity_preserves_unit_price_and_adds_transaction_total():
    single = calculate_price(parse_item_text("?gs buy potion of healing common consumable 2d4+2 healing"))
    quantity = calculate_price(parse_item_text("?gs buy potion of healing common consumable 2d4+2 healing qty 3"))

    assert quantity.final_price == single.final_price
    assert quantity.quantity == 3
    assert quantity.transaction_total == single.final_price * 3


@pytest.mark.parametrize(
    ("single_command", "quantity_command"),
    [
        (
            "?gs buy +1 sword uncommon weapon",
            "?gs buy +1 sword uncommon weapon qty 4",
        ),
        (
            "?gs buy wand of sparks rare complex 8d6",
            "?gs buy wand of sparks rare complex 8d6 count 8",
        ),
        (
            "?gs buy cloak of utility uncommon utility reusable utility",
            "?gs buy cloak of utility uncommon utility reusable utility quantity 12",
        ),
        (
            "?gs buy wand of fireballs rare complex 8d6 aoe 7 charges",
            "?gs buy wand of fireballs rare complex 8d6 aoe 7 charges qty 2",
        ),
        (
            "?gs sell +1 sword uncommon weapon at 75%",
            "?gs sell +1 sword uncommon weapon qty 5 at 75%",
        ),
    ],
)
def test_quantity_keeps_unit_price_and_adds_total_across_pricing_inputs(single_command, quantity_command):
    single = calculate_price(parse_item_text(single_command))
    quantity = calculate_price(parse_item_text(quantity_command))

    assert quantity.final_price == single.final_price
    assert quantity.list_price == single.list_price
    assert quantity.transaction_total == quantity.final_price * quantity.quantity


@pytest.mark.parametrize(
    ("single_command", "quantity_command"),
    [
        (
            "?gs buy alchemy jug uncommon utility reusable utility",
            "?gs buy alchemy jug uncommon utility reusable utility qty 2",
        ),
        (
            "?gs buy boots of the winding path uncommon utility reusable utility",
            "?gs buy boots of the winding path uncommon utility reusable utility quantity 3",
        ),
        (
            "?gs buy wand of wonder rare complex broad 7 charges",
            "?gs buy wand of wonder rare complex broad 7 charges count 4",
        ),
        (
            "?gs buy deck of illusions uncommon complex broad utility",
            "?gs buy deck of illusions uncommon complex broad utility qty 7",
        ),
    ],
)
def test_weird_item_quantities_keep_unit_price_and_add_total(single_command, quantity_command):
    single = calculate_price(parse_item_text(single_command))
    quantity = calculate_price(parse_item_text(quantity_command))

    assert quantity.final_price == single.final_price
    assert quantity.list_price == single.list_price
    assert quantity.transaction_total == quantity.final_price * quantity.quantity
