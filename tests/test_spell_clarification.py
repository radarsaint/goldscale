from goldscale.clarification import PendingAppraisals, cancel_appraisal, continue_appraisal, start_appraisal
from goldscale.parser import find_damage_or_healing, find_spell_reference


KEY = (1, 10, 100)


def start_cloudkill_pending(pending: PendingAppraisals):
    return start_appraisal(
        """buy
Staff of Rotting Vapors
Staff, rare
This staff has 6 charges. You can expend 1 charge to cast cloudkill.""",
        KEY,
        pending,
        now=0,
    )


def test_item_references_cloudkill_and_asks_for_spell_description():
    pending = PendingAppraisals()
    output = start_cloudkill_pending(pending)

    assert "I found **Staff of Rotting Vapors**." in output
    assert "Spell reference: cloudkill" in output
    assert "I need the spell description" in output
    assert "Paste the Cloudkill spell text" in output

    assert "Final Price" not in output
    assert "8d6" not in output
    assert "5d8" not in output
    assert "minor" not in output
    assert "reusable" not in output
    assert "broad" not in output
    assert "?gs buy Staff of Rotting Vapors" not in output


def test_cloudkill_followup_extracts_explicit_damage_aoe_charges_and_warns():
    pending = PendingAppraisals()
    start_cloudkill_pending(pending)

    output = continue_appraisal(
        """Cloudkill
A 20-foot-radius sphere of poisonous, yellow-green fog appears within range.
When a creature enters the spell's area for the first time on a turn or starts its turn there, it makes a Constitution saving throw.
On a failed save, it takes 5d8 poison damage.""",
        KEY,
        pending,
        now=10,
    )

    assert "Staff of Rotting Vapors" in output
    assert "Damage: 5d8" in output
    assert "AoE: Yes" in output
    assert "Charges: 6" in output
    assert "Final Price" in output
    assert "108,000 gp" in output
    assert "Ongoing spell effect detected" in output
    assert "Goldscale used one damage instance" in output

    assert "save DC" not in output.lower()
    assert "duration multiplier" not in output.lower()
    assert "concentration multiplier" not in output.lower()
    assert "rounds" not in output.lower()
    assert "10 rounds" not in output.lower()


def test_cloudkill_save_dc_range_duration_and_concentration_are_ignored_for_pricing():
    pending = PendingAppraisals()
    start_cloudkill_pending(pending)

    output = continue_appraisal(
        """Cloudkill
Range: 120 feet
Duration: Concentration, up to 10 minutes
Each creature in a 20-foot-radius sphere makes a DC 15 Constitution saving throw and takes 5d8 poison damage.""",
        KEY,
        pending,
        now=10,
    )

    assert "Damage: 5d8" in output
    assert "AoE: Yes" in output
    assert "108,000 gp" in output
    assert "120" not in output
    assert "DC 15" not in output
    assert "10 minutes" not in output


def test_cure_wounds_spell_text_extracts_healing_without_item_bonus():
    pending = PendingAppraisals()
    output = start_appraisal(
        """buy
Wand of Mercy
Wand, uncommon
This wand has 7 charges. You can expend 1 charge to cast cure wounds.""",
        KEY,
        pending,
        now=0,
    )

    assert "Paste the Cure Wounds spell text" in output

    priced = continue_appraisal("A creature you touch regains 1d8 + 3 hit points.", KEY, pending, now=10)

    assert "Healing: 1d8+3" in priced
    assert "Charges: 7" in priced
    assert "AoE: No" in priced
    assert "Final Price" in priced
    assert "4,200 gp" in priced
    assert "Impact: +3 bonus" not in priced


def test_spell_text_with_no_damage_or_healing_asks_for_utility_strength():
    pending = PendingAppraisals()
    start_appraisal(
        """buy
Wand of Doors
Wand, uncommon
This wand has 7 charges. You can expend 1 charge to cast knock.""",
        KEY,
        pending,
        now=0,
    )

    output = continue_appraisal(
        "Choose an object that you can see within range. The object opens if it is locked.",
        KEY,
        pending,
        now=10,
    )

    assert "I found spell text, but no damage or healing dice" in output
    assert "How useful should this item count in your campaign?" in output
    assert "1. Minor, small or situational" in output
    assert "2. Reusable, useful repeatable effect" in output
    assert "3. Broad, flexible or broadly useful" in output
    assert "Final Price" not in output
    assert "?gs buy" not in output


def test_spell_name_alone_never_prices():
    pending = PendingAppraisals()
    output = start_appraisal(
        """buy
Wand of Fireballs
Wand, rare
This wand has 7 charges. You can cast fireball.""",
        KEY,
        pending,
        now=0,
    )

    assert "I need the spell description" in output
    assert "8d6" not in output
    assert "157,000 gp" not in output
    assert "Final Price" not in output


def test_spell_reference_extraction_accepts_common_cast_phrases():
    examples = {
        "You can cast cloudkill.": "cloudkill",
        "You can cast cure wounds.": "cure wounds",
        "You can cast fireball.": "fireball",
        "You can cast the fireball spell.": "fireball",
        "You can expend 1 charge to cast lightning bolt.": "lightning bolt",
    }

    for text, expected in examples.items():
        assert find_spell_reference(text, None, None) == expected


def test_spell_reference_extraction_ignores_non_spell_cast_words():
    for text in ("casts a shadow", "cast iron", "spell save DC", "spell attack bonus"):
        assert find_spell_reference(text, None, None) is None


def test_spell_dice_extraction_from_pasted_spell_text():
    damage_examples = ("takes 5d8 poison damage", "deals 8d6 fire damage", "takes 3d10 necrotic damage")
    healing_examples = (
        "regains 1d8 + 3 hit points",
        "regain 2d4+2 hit points",
        "heals 4d4 + 4 hit points",
    )

    for text in damage_examples:
        assert find_damage_or_healing(text)[0] is not None
        assert find_damage_or_healing(text)[1] is None

    for text in healing_examples:
        assert find_damage_or_healing(text)[0] is None
        assert find_damage_or_healing(text)[1] is not None


def test_other_user_channel_and_cancel_do_not_complete_pending_spell_appraisal():
    pending = PendingAppraisals()
    start_cloudkill_pending(pending)

    assert continue_appraisal("Cloudkill takes 5d8 poison damage.", (1, 10, 101), pending, now=10) is None
    assert continue_appraisal("Cloudkill takes 5d8 poison damage.", (1, 11, 100), pending, now=10) is None
    assert cancel_appraisal(KEY, pending) == "Canceled the pending appraisal."
    assert continue_appraisal("Cloudkill takes 5d8 poison damage.", KEY, pending, now=20) is None
