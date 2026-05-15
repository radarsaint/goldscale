import re
from dataclasses import dataclass, field
from typing import Optional


# These are pricing controls, not item-description guesses.
# Do not add flavor synonyms here.
UTILITY_IMPACT = {
    "minor": 4,
    "reusable": 6,
    "broad": 8,
}


TYPE_TO_CATEGORY = {
    "potion": "consumable",
    "scroll": "consumable",

    "weapon": "weapon / armor",
    "armor": "weapon / armor",
    "armour": "weapon / armor",
    "shield": "weapon / armor",
    "sword": "weapon / armor",
    "axe": "weapon / armor",
    "bow": "weapon / armor",
    "mace": "weapon / armor",
    "dagger": "weapon / armor",
    "spear": "weapon / armor",
    "crossbow": "weapon / armor",
    "longsword": "weapon / armor",
    "shortsword": "weapon / armor",
    "greatsword": "weapon / armor",

    "wand": "complex",
    "staff": "complex",
    "rod": "complex",

    "cloak": "utility",
    "ring": "utility",
    "boots": "utility",
    "gloves": "utility",
    "gauntlets": "utility",
    "amulet": "utility",
    "helm": "utility",
    "hat": "utility",
    "belt": "utility",
    "bracers": "utility",
    "brooch": "utility",
}


CATEGORY_ALIASES = {
    "consumable": "consumable",
    "weapon": "weapon / armor",
    "wep": "weapon / armor",
    "armor": "weapon / armor",
    "armour": "weapon / armor",
    "weapon / armor": "weapon / armor",
    "weapon armor": "weapon / armor",
    "utility": "utility",
    "util": "utility",
    "complex": "complex",
}


AVRAE_LABELS = {
    "attunement",
    "requires attunement",
    "description",
    "regaining charges",
    "item",
    "dmg",
    "dmg-2024",
}


@dataclass
class ItemData:
    item_name: Optional[str] = None
    rarity: Optional[str] = None
    unsupported_rarity: Optional[str] = None
    category: Optional[str] = None
    category_source: Optional[str] = None
    bonus: Optional[int] = None
    damage: Optional[str] = None
    healing: Optional[str] = None
    utility: Optional[str] = None
    aoe: bool = False
    charges: Optional[int] = None
    quantity: Optional[int] = None
    official_price: Optional[int] = None
    sell_rate: Optional[float] = None
    sell_rate_error: Optional[str] = None
    sell_rate_retry: Optional[str] = None
    sell_rate_retry_command: Optional[str] = None
    mode: str = "buy"
    randomized: bool = False
    complex_partial_bonus: bool = False
    warnings: list[str] = field(default_factory=list)


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def text_before_description(text: str) -> str:
    return re.split(
        r"\b(description|attunement|requires attunement|regaining charges|while holding it|this item|this wand|this staff|this weapon)\b",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]


def title_item_name(name: str) -> str:
    name = re.sub(r"^[,;:\s]+|[,;:\s]+$", "", name)
    name = normalize_spaces(name)

    if not name:
        return "Unnamed Item"

    small_words = {"of", "the", "and", "a", "an", "in", "on", "with"}
    result = []

    for index, word in enumerate(name.split()):
        if re.fullmatch(r"\+[123]", word):
            result.append(word)
            continue

        lower = word.lower()
        if index > 0 and lower in small_words:
            result.append(lower)
        else:
            result.append(word[:1].upper() + word[1:])

    return " ".join(result)


def remove_old_prefix_accidents(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^\s*!price\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*\?gs\s+", "", text, flags=re.IGNORECASE)
    return text.strip()


def split_mode(text: str) -> tuple[str, str]:
    stripped = text.strip()

    if re.match(r"^sell\b", stripped, flags=re.IGNORECASE):
        return "sell", re.sub(r"^sell\b", "", stripped, flags=re.IGNORECASE).strip()

    if re.match(r"^(buy|price)\b", stripped, flags=re.IGNORECASE):
        return "buy", re.sub(r"^(buy|price)\b", "", stripped, flags=re.IGNORECASE).strip()

    return "buy", stripped


def strip_known_speaker_prefix(text: str) -> str:
    return normalize_spaces(text)


def find_rarity(text: str) -> tuple[Optional[str], Optional[str]]:
    lower = text.lower()

    if re.search(r"\blegendary\b", lower):
        return None, "legendary"

    if re.search(r"\bartifact\b", lower):
        return None, "artifact"

    if re.search(r"\bvery\s+rare\b", lower) or re.search(r"\bveryrare\b", lower) or re.search(r"\bvr\b", lower):
        return "very rare", None

    for rarity in ("uncommon", "common", "rare"):
        if re.search(rf"\b{rarity}\b", lower):
            return rarity, None

    return None, None


def find_explicit_category(text: str) -> tuple[Optional[str], Optional[str]]:
    lower = text.lower()

    explicit_patterns = [
        ("weapon / armor", "explicit category"),
        ("weapon armor", "explicit category"),
        ("consumable", "explicit category"),
        ("utility", "explicit category"),
        ("complex", "explicit category"),
        ("weapon", "explicit category"),
        ("wep", "explicit category"),
        ("armor", "explicit category"),
        ("armour", "explicit category"),
    ]

    for word, source in explicit_patterns:
        if re.search(rf"\b{re.escape(word)}\b", lower):
            return CATEGORY_ALIASES[word], source

    return None, None


def find_category_from_type(text: str, item_name: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    search_space = f"{item_name or ''} {text}".lower()

    for type_word, category in TYPE_TO_CATEGORY.items():
        if re.search(rf"\b{re.escape(type_word)}\b", search_space):
            return category, f'inferred from "{type_word}"'

    return None, None


def find_charges(text: str) -> Optional[int]:
    lower = text.lower()

    patterns = [
        r"\bhas\s+(\d+)\s+charges?\b",
        r"\b(\d+)\s+charges?\b",
        r"\bcharges?\s*[:=]?\s*(\d+)\b",
        r"\b(\d+)\s+uses?\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            return int(match.group(1))

    return None


def find_quantity(text: str) -> Optional[int]:
    lower = text.lower()
    match = re.search(r"\b(?:quantity|qty|count)\s*[:=]?\s*(\d+)\b", lower)

    if match:
        return int(match.group(1))

    return None


def find_official_price(text: str) -> Optional[int]:
    lower = text.lower()
    match = re.search(
        r"\b(?:official price|official|listed price|list price)\s*[:=]?\s*([\d,]+)\s*(?:gp)?\b",
        lower,
    )

    if match:
        return int(match.group(1).replace(",", ""))

    return None


def find_sell_rate(text: str) -> tuple[Optional[float], Optional[str]]:
    lower = text.lower()

    percent_match = re.search(r"\b(?:at|for|custom)?\s*(\d{1,3})\s*%", lower)
    if percent_match:
        rate = int(percent_match.group(1))

        if rate <= 0 or rate > 100:
            return None, "Sell rate must be between 1% and 100%."

        return rate / 100, None

    bare_match = re.search(r"\b(?:at|for|custom)\s+(\d{1,3})\b", lower)
    if bare_match:
        number = bare_match.group(1)
        return None, f'I found "{number}" but not "{number}%." For sell rates, include the percent sign.'

    return None, None


def sell_rate_error_message(warning: str) -> str:
    if warning == "Sell rate must be between 1% and 100%.":
        return warning

    return "I need the sell rate with a percent sign."


def build_sell_rate_retry_command(body: str, number: str) -> str:
    retry_body = re.sub(
        rf"\b(at|for|custom)\s+{re.escape(number)}\b",
        rf"\1 {number}%",
        body,
        count=1,
        flags=re.IGNORECASE,
    )
    return f"?gs sell {normalize_spaces(retry_body)}"


def item_name_before_pricing_signals(text: str) -> Optional[str]:
    cleaned = normalize_spaces(text)
    if not cleaned:
        return None

    signal_pattern = re.compile(
        r"\b("
        r"common|uncommon|rare|very\s+rare|veryrare|vr|legendary|artifact|"
        r"consumable|utility|complex|weapon\s*/\s*armor|weapon armor|armor|armour|"
        r"\d+d\d+(?:\s*[+-]\s*\d+)?|aoe|area of effect|minor|reusable|broad|"
        r"\d+\s+charges?|charges?\s*[:=]?\s*\d+|"
        r"(?:quantity|qty|count)\s*[:=]?\s*\d+|"
        r"official price|official|at\s+\d{1,3}%?"
        r")\b",
        flags=re.IGNORECASE,
    )
    match = signal_pattern.search(cleaned)

    if not match:
        return None

    candidate = cleaned[:match.start()].strip(" ,;:")
    return candidate or None


def strip_leading_quantity_signal(text: str) -> str:
    return re.sub(r"^\s*(?:quantity|qty|count)\s*[:=]?\s*\d+\s+", "", text, flags=re.IGNORECASE)


def trim_flattened_speaker_text(candidate: str, type_word: str) -> str:
    words = candidate.split()
    lowered_type = type_word.lower()

    for index in range(len(words) - 1, -1, -1):
        if words[index].lower() == lowered_type:
            return " ".join(words[index:])

    return candidate


def remove_dice_expressions(text: str) -> str:
    return re.sub(r"\b\d+d\d+(?:\s*[+-]\s*\d+)?\b", " ", text, flags=re.IGNORECASE)


def find_bonus(text: str) -> Optional[int]:
    # Remove dice expressions first so "1d6 + 1" does not become a +1 item.
    no_dice = remove_dice_expressions(text.lower())

    explicit = re.search(r"\bbonus\s*[:=]?\s*\+?([123])\b", no_dice)
    if explicit:
        return int(explicit.group(1))

    match = re.search(r"(?<![0-9d])\+([123])\b", no_dice)
    if match:
        return int(match.group(1))

    return None


def find_dice_expressions(text: str) -> list[tuple[str, int, int]]:
    results = []

    for match in re.finditer(r"\b\d+d\d+(?:\s*[+-]\s*\d+)?\b", text.lower()):
        expr = match.group(0).replace(" ", "")
        results.append((expr, match.start(), match.end()))

    return results


def dice_is_recharge_or_table_roll(lower: str, start: int, end: int, allow_charge_count_clause: bool = False) -> bool:
    window = lower[max(0, start - 80): min(len(lower), end + 120)]
    after_dice = lower[end: min(len(lower), end + 80)]

    reject_terms = [
        "regains",
        "regain",
        "recharge",
        "charges daily",
        "daily at dawn",
        "expended charges",
        "roll 1d20",
        "roll a d20",
        "on a 1",
        "crumbles",
        "destroyed",
    ]

    if any(term in window for term in reject_terms):
        return True

    if re.match(r"^[\s,]*(beads?|stars?|charges?|uses?)\b", after_dice):
        return True

    # Strongly reject dice whose nearby noun is charges, unless it is clearly damage/healing.
    if "charge" in window and not any(term in window for term in ("damage", "healing", "hit points")):
        if allow_charge_count_clause and re.match(r"^[\s,]*(?:aoe|area of effect)?[\s,]*\d+\s+charges?\b", after_dice):
            return False
        return True

    return False


def find_damage_or_healing(text: str) -> tuple[Optional[str], Optional[str]]:
    lower = text.lower()
    dice_matches = find_dice_expressions(lower)

    for expr, start, end in dice_matches:
        if dice_is_recharge_or_table_roll(lower, start, end):
            continue

        window = lower[max(0, start - 90): min(len(lower), end + 120)]

        if any(term in window for term in ("heal", "healing", "hit points")) and "charge" not in window:
            return None, expr

        if any(term in window for term in ("damage", "dam.", "takes", "deal", "deals")):
            return expr, None

    # Loose command syntax still needs to work:
    # ?gs buy wand of fireballs, rare complex, 8d6 aoe, 7 charges
    # If this is not an Avrae/rules-text paste, accept the first non-recharge dice as damage.
    looks_like_paste = bool(re.search(r"\b(description|attunement|requires attunement|regaining charges)\b", lower))

    if not looks_like_paste:
        for expr, start, end in dice_matches:
            if not dice_is_recharge_or_table_roll(lower, start, end, allow_charge_count_clause=True):
                if re.search(rf"{re.escape(expr)}\s*(healing|heal)", lower):
                    return None, expr
                return expr, None

    return None, None


def find_aoe(text: str) -> bool:
    lower = text.lower()

    safe_patterns = [
        r"\baoe\b",
        r"\barea of effect\b",
        r"\b\d+\s*-?\s*foot\s+radius\b",
        r"\bradius\b",
        r"\bsphere\b",
        r"\bcone\b",
        r"\bcube\b",
        r"\bcylinder\b",
        r"\b\d+\s*-?\s*foot\s+line\b",
        r"\beach creature in\b",
        r"\beach creature within\b",
        r"\bcreatures within\b",
        r"\ball creatures within\b",
    ]

    return any(re.search(pattern, lower) for pattern in safe_patterns)


def find_utility(text: str) -> Optional[str]:
    lower = text.lower()

    # Explicit adjacent forms work anywhere, including after a pasted description.
    adjacent_patterns = [
        r"\b(minor|reusable|broad)\s+utility\b",
        r"\butility\s*[:=,]?\s*(minor|reusable|broad)\b",
    ]

    for pattern in adjacent_patterns:
        match = re.search(pattern, lower)
        if match:
            if match.group(1) in UTILITY_IMPACT:
                return match.group(1)
            if match.group(2) in UTILITY_IMPACT:
                return match.group(2)

    # Loose shorthand works only before Avrae description text.
    # This lets "?gs buy cloak, uncommon utility, reusable" work, but avoids reading item prose as a tier.
    pre_description = re.split(r"\bdescription\b", lower, maxsplit=1)[0]

    for tier in UTILITY_IMPACT:
        if re.search(rf"\b{tier}\b", pre_description):
            return tier

    return None


def find_randomized_item_markers(text: str) -> bool:
    lower = text.lower()

    markers = [
        "determined by rolling",
        "roll on",
        "effects table",
        "effect determined",
        "determines randomly",
        "determined randomly",
        "randomly which",
        "random effect",
    ]

    return any(marker in lower for marker in markers)


def clean_lines_after_mode(text: str) -> list[str]:
    cleaned = remove_old_prefix_accidents(text)
    _, cleaned = split_mode(cleaned)

    lines = []
    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.lower() in AVRAE_LABELS:
            continue

        lines.append(line)

    return lines


def extract_item_name(text: str) -> Optional[str]:
    cleaned = remove_old_prefix_accidents(text)
    _, cleaned = split_mode(cleaned)

    lines = clean_lines_after_mode(text)

    # Avrae multiline pattern:
    # Wand of Wonder
    # Wand, rare
    for index, line in enumerate(lines[:-1]):
        next_line = lines[index + 1]
        if re.match(r"^(wand|weapon|armor|armour|potion|scroll|staff|rod|ring|cloak|shield)[,\s]+(?:common|uncommon|rare|very\s+rare)\b", next_line, flags=re.IGNORECASE):
            return title_item_name(strip_known_speaker_prefix(line))

    # If first cleaned line looks title-like, use it.
    if lines:
        first = strip_leading_quantity_signal(strip_known_speaker_prefix(lines[0]))
        if not re.search(r"\b(description|attunement|requires attunement|this item|this wand|this weapon)\b", first, flags=re.IGNORECASE):
            signal_candidate = item_name_before_pricing_signals(first)
            if signal_candidate:
                return title_item_name(signal_candidate)
            if "," in first:
                candidate = first.split(",", 1)[0]
                if candidate.strip():
                    return title_item_name(candidate)
            if len(first) <= 90:
                return title_item_name(first)

    # Flattened Avrae pattern:
    # DM radar Wand of Wonder Wand, rare Attunement...
    flat = normalize_spaces(cleaned)
    type_words = "|".join(re.escape(word) for word in ["wand", "weapon", "armor", "armour", "potion", "scroll", "staff", "rod", "ring", "cloak", "shield"])
    match = re.search(
        rf"^(.+?)\s+({type_words})\s*,\s*(common|uncommon|rare|very\s+rare)\b",
        flat,
        flags=re.IGNORECASE,
    )

    if match:
        candidate = trim_flattened_speaker_text(strip_known_speaker_prefix(match.group(1)), match.group(2))
        return title_item_name(candidate)

    return None


def remove_known_signals_for_name(text: str) -> str:
    cleaned = remove_old_prefix_accidents(text)
    _, cleaned = split_mode(cleaned)

    # Remove everything after common Avrae rule prose starts.
    cleaned = re.split(
        r"\b(description|attunement|requires attunement|regaining charges|this wand|this item|this weapon|while holding it)\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # Remove labels and pricing signals.
    cleaned = re.sub(r"\b(item|rarity|category|damage|healing|utility|charges|charge|official price|official)\s*[:=]", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bvery\s+rare\b|\bveryrare\b|\bvr\b|\buncommon\b|\bcommon\b|\brare\b|\blegendary\b|\bartifact\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(consumable|utility|complex|weapon\s*/\s*armor|weapon armor|weapon|armor|armour)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d+d\d+(?:\s*[+-]\s*\d+)?\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?<![0-9d])\+[123]\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d+\s*(?:charges?|uses?)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:has\s+)?\d+\s+charges?\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:quantity|qty|count)\s*[:=]?\s*\d+\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(aoe|area of effect|minor|reusable|broad)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:at|for|custom)?\s*\d{1,3}\s*%", " ", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"[,;:|]+", " ", cleaned)
    cleaned = normalize_spaces(cleaned)

    return cleaned


def trim_repeated_category_from_bonus_name(name: str) -> str:
    if not re.match(r"^\+[123]\b", name, flags=re.IGNORECASE):
        return name

    return re.sub(r"\s+(weapon|armor|armour)$", "", name, flags=re.IGNORECASE)


def parse_item_text(raw: str) -> ItemData:
    text = remove_old_prefix_accidents(raw)
    mode, body = split_mode(text)

    data = ItemData(mode=mode)

    data.item_name = extract_item_name(text)
    data.rarity, data.unsupported_rarity = find_rarity(body)

    explicit_category, explicit_source = find_explicit_category(text_before_description(body))
    data.category = explicit_category
    data.category_source = explicit_source

    data.charges = find_charges(body)
    data.quantity = find_quantity(body)
    data.official_price = find_official_price(body)
    data.bonus = find_bonus(body)
    data.damage, data.healing = find_damage_or_healing(body)
    data.aoe = find_aoe(body)
    data.utility = find_utility(body)
    data.randomized = find_randomized_item_markers(body)

    if data.mode == "sell":
        data.sell_rate, warning = find_sell_rate(body)
        if warning:
            data.sell_rate_error = sell_rate_error_message(warning)
            data.warnings.append(warning)
            match = re.search(r'"(\d{1,3})"', warning)
            if match:
                data.sell_rate_retry = match.group(1)
                data.sell_rate_retry_command = build_sell_rate_retry_command(body, data.sell_rate_retry)
        if data.sell_rate is None and not data.sell_rate_error:
            data.sell_rate = 0.50

    if not data.item_name:
        candidate = remove_known_signals_for_name(body)
        data.item_name = title_item_name(candidate) if candidate else None

    if data.category is None:
        inferred_category, source = find_category_from_type(text_before_description(body), data.item_name)
        data.category = inferred_category
        data.category_source = source

    if data.item_name and data.category_source == "explicit category":
        data.item_name = title_item_name(trim_repeated_category_from_bonus_name(data.item_name))

    if (
        data.category == "complex"
        and data.charges
        and data.bonus is not None
        and data.damage is None
        and data.healing is None
        and data.utility is None
    ):
        data.complex_partial_bonus = True

    return data
