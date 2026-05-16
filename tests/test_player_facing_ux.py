from goldscale.clarification import PendingAppraisals, continue_appraisal, start_appraisal


KEY = (1, 10, 100)


def test_bare_item_name_asks_for_description_not_programmer_retry():
    pending = PendingAppraisals()
    output = start_appraisal("buy wand of wonder", KEY, pending, now=0)

    assert "I need the item description" in output
    assert "Paste the item text from Avrae or D&D Beyond" in output
    assert "?gs buy Wand of Wonder, rare wand, broad utility" not in output
    assert "impact" not in output.lower()
    assert "formula category" not in output.lower()
    assert "complex" not in output.lower()


def test_missing_spell_description_asks_for_spell_text_not_command_syntax():
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

    assert "I need the spell description" in output
    assert "Paste the Cloudkill spell text" in output
    assert "Try:" not in output
    assert "?gs buy Staff of Rotting Vapors" not in output


def test_missing_utility_strength_asks_plain_language_question():
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

    output = continue_appraisal("This table has randomized effects and no damage dice.", KEY, pending, now=10)

    assert output == "How useful should this item count in your campaign: minor, reusable, or broad?"
    assert "Try:" not in output
    assert "?gs buy" not in output


def test_output_avoids_try_this_command_as_primary_missing_info_solution():
    pending = PendingAppraisals()
    outputs = [
        start_appraisal("buy staff of power", KEY, pending, now=0),
        start_appraisal("buy alchemy jug", KEY, pending, now=1),
        start_appraisal("buy necklace of fireballs", KEY, pending, now=2),
    ]

    for output in outputs:
        assert "I need the item description" in output
        assert "Try:" not in output
        assert "minor utility" not in output
        assert "8d6 aoe" not in output
