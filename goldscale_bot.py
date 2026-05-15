from goldscale.bot import COMMAND_PREFIX, TOKEN, bot, run_bot
from goldscale.formatting import (
    build_retry_example,
    build_retry_options,
    format_missing,
    format_result,
    formula_text,
    help_text,
    impact_retry_text,
    read_as_block,
)
from goldscale.parser import (
    ItemData,
    CATEGORY_ALIASES,
    AVRAE_LABELS,
    TYPE_TO_CATEGORY,
    UTILITY_IMPACT,
    clean_lines_after_mode,
    dice_is_recharge_or_table_roll,
    extract_item_name,
    find_aoe,
    find_bonus,
    find_category_from_type,
    find_charges,
    find_damage_or_healing,
    find_dice_expressions,
    find_explicit_category,
    find_official_price,
    find_randomized_item_markers,
    find_rarity,
    find_sell_rate,
    find_utility,
    normalize_spaces,
    parse_item_text,
    remove_dice_expressions,
    remove_known_signals_for_name,
    remove_old_prefix_accidents,
    split_mode,
    strip_known_speaker_prefix,
    text_before_description,
    title_item_name,
)
from goldscale.pricing import (
    PricingResult,
    RARITY_GPI,
    average_dice,
    calculate_price,
    clean_shop_value,
    has_impact,
    missing_fields,
)


if __name__ == "__main__":
    run_bot()
