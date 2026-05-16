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
