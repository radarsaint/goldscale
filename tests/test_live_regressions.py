from goldscale.clarification import PendingAppraisals, continue_appraisal, start_appraisal


KEY = (1, 10, 100)


def test_flame_tongue_prices_850_gp_without_light_radius_aoe():
    pending = PendingAppraisals()
    output = start_appraisal(
        """buy
Flame Tongue
Weapon (Any Melee Weapon), rare
Description
These flames shed Bright Light in a 40-foot radius and Dim Light for an additional 40 feet. While the weapon is ablaze, it deals an extra 2d6 Fire damage on a hit.""",
        KEY,
        pending,
        now=0,
    )

    assert "Damage: 2d6" in output
    assert "AoE: No" in output
    assert "Final Price" in output
    assert "850 gp" in output
    assert "AoE ×4" not in output
    assert "3,400 gp" not in output


def test_necklace_of_fireballs_paste_asks_for_beads_and_damage_dice():
    pending = PendingAppraisals()
    output = start_appraisal(
        """buy
Necklace of Fireballs
Wondrous Item, rare
Description
This necklace has 1d6 + 3 beads hanging from it. You can take a Magic action to detach a bead and throw it up to 60 feet away. When it reaches the end of its trajectory, the bead detonates as a level 3 Fireball (save DC 15).

You can hurl multiple beads, or even the whole necklace, at one time. When you do so, increase the damage of the Fireball by 1d6 for each bead after the first (maximum 12d6).""",
        KEY,
        pending,
        now=0,
    )

    assert "I found **Necklace of Fireballs**" in output
    assert "I need two details before I can price it" in output
    assert "How many beads should I price" in output
    assert "what damage dice should I use" in output
    assert "Impact: 1d6" not in output
    assert "Final Price" not in output
    assert "525 gp" not in output
    assert "Formula Category: Utility Item" not in output


def test_necklace_followup_prices_explicit_beads_and_damage():
    pending = PendingAppraisals()
    start_appraisal(
        """buy
Necklace of Fireballs
Wondrous Item, rare
Description
This necklace has 1d6 + 3 beads hanging from it. You can take a Magic action to detach a bead and throw it up to 60 feet away. When it reaches the end of its trajectory, the bead detonates as a level 3 Fireball (save DC 15).

You can hurl multiple beads, or even the whole necklace, at one time. When it does so, increase the damage of the Fireball by 1d6 for each bead after the first (maximum 12d6).""",
        KEY,
        pending,
        now=0,
    )

    output = continue_appraisal("6 beads, 8d6", KEY, pending, now=10)

    assert "Damage: 8d6" in output
    assert "AoE: Yes" in output
    assert "Charges: 6" in output
    assert "Final Price" in output
    assert "134,500 gp" in output
