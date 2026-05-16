from goldscale.clarification import has_ongoing_spell_effect
from goldscale.parser import find_bonus, find_charges, find_damage_or_healing, parse_item_text


def no_price_numbers(text: str):
    data = parse_item_text(f"?gs buy Test Item rare wand Description\n{text}")
    damage, healing = find_damage_or_healing(text)
    return data, damage, healing


def test_non_impact_numbers_are_ignored_as_damage_healing_charges_and_bonus():
    examples = [
        "save DC 15",
        "range 120 feet",
        "duration 1 minute",
        "components V S M",
        "spell level 3",
        "AC 20",
        "hit points 200",
        "speed 30 feet",
        "weighs 5 pounds",
        "1d6 + 3 beads",
        "1d4 patches",
        "roll 1d20",
        "on a 1",
    ]

    for text in examples:
        data, damage, healing = no_price_numbers(text)
        assert damage is None, text
        assert healing is None, text
        assert data.charges is None, text
        assert find_bonus(text) is None, text


def test_explicit_fixed_use_counts_are_accepted():
    assert find_charges("6 beads") == 6
    assert find_charges("6 uses") == 6
    assert find_charges("6 charges") == 6


def test_random_count_dice_are_not_fixed_use_counts():
    assert find_charges("1d6 + 3 beads") is None
    assert find_charges("1d4 patches") is None


def test_ongoing_spell_warning_detection_triggers_only_for_repeated_effects():
    repeated = [
        "starts its turn",
        "enters the area for the first time on a turn",
        "at the start of each turn",
        "at the end of each turn",
        "duration",
        "concentration",
        "each round",
    ]
    one_shot = ["takes 8d6 fire damage once", "when you hit", "on a hit"]

    for text in repeated:
        assert has_ongoing_spell_effect(text), text

    for text in one_shot:
        assert not has_ongoing_spell_effect(text), text


def test_healing_modifier_does_not_become_item_bonus():
    text = "A creature you touch regains 1d8 + 3 hit points."
    damage, healing = find_damage_or_healing(text)

    assert damage is None
    assert healing == "1d8+3"
    assert find_bonus(text) is None
