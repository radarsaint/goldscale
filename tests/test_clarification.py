from goldscale.clarification import (
    PendingAppraisals,
    cancel_appraisal,
    continue_appraisal,
    start_appraisal,
)


KEY = (1, 10, 100)


def test_bare_item_name_asks_for_description_not_retry_commands():
    pending = PendingAppraisals()
    output = start_appraisal("buy wand of wonder", KEY, pending, now=0)

    assert "I found **Wand of Wonder**, but I need the item description before I can price it." in output
    assert "Paste the item text from Avrae or D&D Beyond after:" in output
    assert "minor utility" not in output
    assert "reusable utility" not in output
    assert "broad utility" not in output
    assert "8d6 aoe" not in output


def test_wand_of_wonder_pasted_description_asks_for_utility_strength():
    pending = PendingAppraisals()
    output = start_appraisal(
        """buy
Wand of Wonder
Wand, rare
Description
This wand has 7 charges. Roll on the effects table.""",
        KEY,
        pending,
        now=0,
    )

    assert "How useful should this item count in your campaign: minor, reusable, or broad?" in output


def test_answering_broad_completes_wand_of_wonder_pricing():
    pending = PendingAppraisals()
    start_appraisal(
        """buy
Wand of Wonder
Wand, rare
Description
This wand has 7 charges. Roll on the effects table.""",
        KEY,
        pending,
        now=0,
    )

    output = continue_appraisal("broad", KEY, pending, now=10)

    assert "**Item:** Wand of Wonder" in output
    assert "Broad utility = 8 impact; charges" in output
    assert "**Final Price**\n**11,000 gp**" in output


def test_necklace_of_fireballs_asks_for_beads_and_damage_dice():
    pending = PendingAppraisals()
    output = start_appraisal(
        """buy
Necklace of Fireballs
Wondrous Item, rare
Description
This necklace has 1d6 + 3 beads hanging from it. It detonates as a level 3 Fireball. Increase the damage by 1d6 for each bead after the first.""",
        KEY,
        pending,
        now=0,
    )

    assert "I found **Necklace of Fireballs**" in output
    assert "I need two details before I can price it" in output
    assert "How many beads should I price, and what damage dice should I use?" in output
    assert "**Final Price**" not in output


def test_answering_beads_and_damage_completes_necklace_pricing():
    pending = PendingAppraisals()
    start_appraisal(
        """buy
Necklace of Fireballs
Wondrous Item, rare
Description
This necklace has 1d6 + 3 beads hanging from it. It detonates as a level 3 Fireball. Increase the damage by 1d6 for each bead after the first.""",
        KEY,
        pending,
        now=0,
    )

    output = continue_appraisal("6 beads, 8d6", KEY, pending, now=10)

    assert "**Item:** Necklace of Fireballs" in output
    assert "Formula Category: Complex Multi-Ability Magic Item" in output
    assert "Impact: 8d6 AoE" in output
    assert "× 6 charges" in output
    assert "**Final Price**\n**134,500 gp**" in output


def test_missing_rarity_clarification_completes_pricing():
    pending = PendingAppraisals()
    output = start_appraisal("buy +1 sword weapon", KEY, pending, now=0)

    assert output == "What rarity is this item?"

    priced = continue_appraisal("uncommon", KEY, pending, now=10)

    assert "**Item:** +1 Sword" in priced
    assert "**Final Price**\n**1,200 gp**" in priced


def test_missing_item_type_clarification_completes_pricing():
    pending = PendingAppraisals()
    output = start_appraisal("buy +1 sword uncommon", KEY, pending, now=0)

    assert output.startswith("What kind of item is this:")

    priced = continue_appraisal("weapon", KEY, pending, now=10)

    assert "**Item:** +1 Sword" in priced
    assert "**Final Price**\n**1,200 gp**" in priced


def test_missing_utility_strength_clarification_completes_pricing():
    pending = PendingAppraisals()
    output = start_appraisal("buy alchemy jug uncommon wondrous item", KEY, pending, now=0)

    assert output == "How useful should this item count in your campaign: minor, reusable, or broad?"

    priced = continue_appraisal("reusable", KEY, pending, now=10)

    assert "**Item:** Alchemy Jug" in priced
    assert "Reusable utility = 6 impact" in priced
    assert "**Final Price**\n**350 gp**" in priced


def test_cancel_clears_pending_appraisal():
    pending = PendingAppraisals()
    start_appraisal("buy wand of wonder", KEY, pending, now=0)

    assert cancel_appraisal(KEY, pending) == "Canceled the pending appraisal."
    assert continue_appraisal("broad", KEY, pending, now=10) is None


def test_pending_appraisals_are_keyed_by_user_and_channel():
    pending = PendingAppraisals()
    other_user = (1, 10, 101)
    other_channel = (1, 11, 100)

    start_appraisal("buy wand of wonder", KEY, pending, now=0)

    assert continue_appraisal("broad", other_user, pending, now=10) is None
    assert continue_appraisal("broad", other_channel, pending, now=10) is None
    assert continue_appraisal("broad", KEY, pending, now=10) is not None


def test_pending_appraisals_expire():
    pending = PendingAppraisals()
    start_appraisal("buy wand of wonder", KEY, pending, now=0)

    assert continue_appraisal("broad", KEY, pending, now=301) is None


def test_item_references_cloudkill_and_asks_for_spell_description():
    pending = PendingAppraisals()
    output = start_appraisal(
        """buy
Staff of Rotting Vapors
Staff, rare
This staff has 6 charges. You can expend 1 charge to cast cloudkill.""",
        KEY,
        pending,
        now=0,
    )

    assert "I found **Staff of Rotting Vapors**." in output
    assert "Rare staff" in output
    assert "6 charges" in output
    assert "Spell reference: cloudkill" in output
    assert "I need the spell description before I can price the spell effect." in output
    assert "Paste the Cloudkill spell text." in output
    assert "**Final Price**" not in output


def test_pasted_cloudkill_text_completes_price_with_warning():
    pending = PendingAppraisals()
    start_appraisal(
        """buy
Staff of Rotting Vapors
Staff, rare
This staff has 6 charges. You can expend 1 charge to cast cloudkill.""",
        KEY,
        pending,
        now=0,
    )

    output = continue_appraisal(
        """Cloudkill
A 20-foot-radius sphere of poisonous, yellow-green fog appears within range. When a creature enters the spell's area for the first time on a turn or starts its turn there, it makes a Constitution saving throw. On a failed save, it takes 5d8 poison damage.""",
        KEY,
        pending,
        now=10,
    )

    assert "**Item:** Staff of Rotting Vapors" in output
    assert "Formula Category: Complex Multi-Ability Magic Item" in output
    assert "Impact: 5d8 AoE" in output
    assert "× 6 charges" in output
    assert "5d8 average = 22.5; AoE" in output
    assert "**Final Price**\n**108,000 gp**" in output
    assert "Ongoing spell effect detected. Goldscale used one damage instance" in output


def test_cloudkill_save_dc_and_range_are_ignored_except_aoe_shape():
    pending = PendingAppraisals()
    start_appraisal(
        """buy
Staff of Rotting Vapors
Staff, rare
This staff has 6 charges. You can expend 1 charge to cast cloudkill.""",
        KEY,
        pending,
        now=0,
    )

    output = continue_appraisal(
        "Cloudkill has a range of 120 feet and requires a DC 15 Constitution saving throw. A 20-foot-radius sphere appears. A target takes 5d8 poison damage.",
        KEY,
        pending,
        now=10,
    )

    assert "5d8 average = 22.5; AoE" in output
    assert "DC 15" not in output
    assert "120" not in output


def test_cure_wounds_spell_text_extracts_healing_and_prices_with_charges():
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

    assert "Paste the Cure Wounds spell text." in output

    priced = continue_appraisal("Cure Wounds\nA creature you touch regains 1d8 + 3 hit points.", KEY, pending, now=10)

    assert "**Item:** Wand of Mercy" in priced
    assert "Impact: 1d8+3 healing" in priced
    assert "1d8+3 average = 7.5; charges" in priced
    assert "**Final Price**\n**4,200 gp**" in priced


def test_spell_description_with_no_damage_or_healing_asks_for_utility_strength():
    pending = PendingAppraisals()
    start_appraisal(
        """buy
Wand of Doors
Wand, uncommon
This wand has 5 charges. You can expend 1 charge to cast knock.""",
        KEY,
        pending,
        now=0,
    )

    output = continue_appraisal("Knock\nChoose an object that you can see within range. The object unlocks.", KEY, pending, now=10)

    assert "I found spell text, but no damage or healing dice." in output
    assert "How useful should this item count in your campaign: minor, reusable, or broad?" in output


def test_other_user_or_channel_cannot_complete_pending_spell_appraisal():
    pending = PendingAppraisals()
    start_appraisal(
        """buy
Staff of Rotting Vapors
Staff, rare
This staff has 6 charges. You can expend 1 charge to cast cloudkill.""",
        KEY,
        pending,
        now=0,
    )

    assert continue_appraisal("Cloudkill takes 5d8 poison damage.", (1, 10, 101), pending, now=10) is None
    assert continue_appraisal("Cloudkill takes 5d8 poison damage.", (1, 11, 100), pending, now=10) is None


def test_cancel_cancels_pending_spell_appraisal():
    pending = PendingAppraisals()
    start_appraisal(
        """buy
Staff of Rotting Vapors
Staff, rare
This staff has 6 charges. You can expend 1 charge to cast cloudkill.""",
        KEY,
        pending,
        now=0,
    )

    assert cancel_appraisal(KEY, pending) == "Canceled the pending appraisal."
    assert continue_appraisal("Cloudkill takes 5d8 poison damage.", KEY, pending, now=10) is None
