"""Independent rebuild of commanderpowermeter.com's deck power-level/bracket
scoring engine, based on the methodology published on their "How It Works"
page: a 0-100 additive score across 7 factors, mapped to the official WotC
Commander Brackets (1-5), with hard gates that can only raise the bracket.

Combo detection (Commander Spellbook) is not yet integrated, so combo-based
win conditions and the "Bracket 5 Classic cEDH" hard gate are not evaluated -
Bracket 5 is only reached via raw score >= 96.
"""

from . import powerlevel_data as data

BRACKET_LABELS = {1: "Exhibition", 2: "Core", 3: "Enhanced", 4: "Masterwork", 5: "cEDH"}


def tag_card(card: dict) -> set[str]:
    """Detect signal categories for a single card from its oracle text/type line."""
    name = card.get("name", "")
    text = card.get("oracle_text") or ""
    type_line = card.get("type_line") or ""
    is_land = "Land" in type_line
    is_creature = "Creature" in type_line
    is_artifact = "Artifact" in type_line

    signals = set()

    if name in data.GAME_CHANGERS:
        signals.add("GAME_CHANGER")

    if name in data.FAST_MANA:
        signals.add("FAST_MANA")

    if data.TUTOR_RE.search(text):
        if data.LAND_TUTOR_RE.search(text):
            signals.add("RAMP")
        else:
            signals.add("TUTOR")

    if not is_land and (is_creature or is_artifact) and data.MANA_ABILITY_RE.search(text):
        signals.add("RAMP")

    if data.TREASURE_RE.search(text):
        signals.add("RAMP")

    if data.REMOVAL_RE.search(text):
        signals.add("REMOVAL")
    if data.WIPE_RE.search(text):
        signals.add("WIPE")
    if data.COUNTERSPELL_RE.search(text):
        signals.add("COUNTERSPELL")
    if data.RECURSION_RE.search(text):
        signals.add("RECURSION")
    if data.PROTECTION_RE.search(text):
        signals.add("PROTECTION")
    if data.DRAW_RE.search(text) and not data.LOOT_RE.search(text):
        signals.add("DRAW")
    if data.IMPULSE_DRAW_RE.search(text):
        signals.add("IMPULSE_DRAW")
    if data.EXTRA_TURN_RE.search(text):
        signals.add("EXTRA_TURN")
    if data.EXTRA_COMBAT_RE.search(text):
        signals.add("EXTRA_COMBAT")
    if data.OVERRUN_RE.search(text):
        signals.add("OVERRUN")
    if data.STAX_RE.search(text):
        signals.add("STAX")
    if data.INFECT_RE.search(text):
        signals.add("INFECT")
    if data.THEFT_RE.search(text):
        signals.add("THEFT")
    if data.BURN_RE.search(text):
        signals.add("BURN")
    if data.TEMPO_RE.search(text):
        signals.add("TEMPO")
    if data.CHAOS_RE.search(text):
        signals.add("CHAOS")

    return signals


def _count_signal(tagged: list[tuple[dict, set, bool]], signal: str) -> int:
    return sum(1 for _, signals, _ in tagged if signal in signals)


def _theme_concentration(tagged: list[tuple[dict, set, bool]]) -> tuple[str | None, float]:
    """Share of non-land, non-commander cards matching the dominant engine theme."""
    nonland = [
        c for c, _, is_cmd in tagged
        if not is_cmd and "Land" not in (c.get("type_line") or "")
    ]
    if not nonland:
        return None, 0.0

    counts = {
        theme: sum(1 for c in nonland if pattern.search(c.get("oracle_text") or ""))
        for theme, pattern in data.ENGINE_THEMES.items()
    }
    dominant = max(counts, key=counts.get)
    if counts[dominant] == 0:
        return None, 0.0
    return dominant, counts[dominant] / len(nonland) * 100


def _synergy_density(tagged: list[tuple[dict, set, bool]]) -> float:
    """Share of engine-theme categories with a meaningful keyword cluster present."""
    nonland = [
        c for c, _, is_cmd in tagged
        if not is_cmd and "Land" not in (c.get("type_line") or "")
    ]
    if not nonland:
        return 0.0

    clusters = sum(
        1
        for pattern in data.ENGINE_THEMES.values()
        if sum(1 for c in nonland if pattern.search(c.get("oracle_text") or "")) >= 3
    )
    return min(100.0, clusters / len(data.ENGINE_THEMES) * 100)


def _avg_cmc_score(avg_cmc: float) -> float:
    """+5 to +30, scaling linearly between an avg CMC of 5.0 and 2.0 (or below)."""
    if avg_cmc <= 2.0:
        return 30.0
    if avg_cmc >= 5.0:
        return 5.0
    return 30.0 + (avg_cmc - 2.0) * (5.0 - 30.0) / 3.0


def _estimated_win_turn(speed_index: float, consistency_index: float) -> int:
    base_turn = 10
    reduction = speed_index / 100 * 5 + consistency_index / 100 * 2
    return max(1, round(base_turn - reduction))


def _execution_points(execution_score: float) -> int:
    if execution_score >= 75:
        return 35
    if execution_score >= 60:
        return 28
    if execution_score >= 45:
        return 22
    if execution_score >= 30:
        return 14
    if execution_score >= 15:
        return 6
    return 0


def score_game_changers(tagged: list[tuple[dict, set, bool]]) -> tuple[int, dict]:
    names = [c["name"] for c, signals, _ in tagged if "GAME_CHANGER" in signals]
    points = {0: 0, 1: 3, 2: 6, 3: 9}.get(len(names), 12)
    return points, {"count": len(names), "cards": names}


def score_tutors(tagged: list[tuple[dict, set, bool]]) -> tuple[int, dict]:
    """Tutors weighted by CMC (cheaper = more dangerous) and scope (broad vs
    type-restricted). Scaled so the published B5 gate value (weighted >= 5.5)
    lands near the +20 cap.
    """
    cards = []
    weighted_total = 0.0
    for card, signals, _ in tagged:
        if "TUTOR" not in signals:
            continue
        cmc = card.get("cmc") or 0
        if cmc <= 1:
            cmc_mult = 1.0
        elif cmc == 2:
            cmc_mult = 0.9
        elif cmc == 3:
            cmc_mult = 0.7
        elif cmc == 4:
            cmc_mult = 0.35
        else:
            cmc_mult = 0.2

        text = card.get("oracle_text") or ""
        scope_mult = 1.0 if data.TUTOR_BROAD_RE.search(text) else 0.7

        weight = cmc_mult * scope_mult
        weighted_total += weight
        cards.append({"name": card["name"], "weight": round(weight, 2)})

    points = round(min(20.0, weighted_total / 5.5 * 20), 2)
    return points, {"weighted_count": round(weighted_total, 2), "cards": cards}


def score_fast_mana(tagged: list[tuple[dict, set, bool]]) -> tuple[int, dict]:
    """Piecewise-linear through the published anchors (2->+5, 5->+13, 8->+20).
    Sol Ring is excluded from the count as the universal baseline.
    """
    names = [
        c["name"] for c, signals, _ in tagged
        if "FAST_MANA" in signals and c["name"] != "Sol Ring"
    ]
    count = len(names)
    anchors = [(0, 0), (2, 5), (5, 13), (8, 20)]
    if count >= anchors[-1][0]:
        points = float(anchors[-1][1])
    else:
        points = float(anchors[-1][1])
        for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
            if x0 <= count <= x1:
                points = y0 + (y1 - y0) * (count - x0) / (x1 - x0)
                break
    return round(points, 2), {"count": count, "cards": names}


def score_mana_base(tagged: list[tuple[dict, set, bool]], color_identity: list[str]) -> tuple[int, dict]:
    """Fixing-land density relative to color count. Mono-colored decks don't
    need fixing, so they score the full +10.
    """
    color_count = max(1, len(color_identity or []))
    fixing = []
    for card, _, _ in tagged:
        type_line = card.get("type_line") or ""
        if "Land" not in type_line:
            continue
        text = card.get("oracle_text") or ""
        if data.FIXING_LAND_RE.search(text) or data.LAND_TUTOR_RE.search(text):
            fixing.append(card["name"])

    if color_count <= 1:
        points = 10.0
    else:
        needed = (color_count - 1) * 4
        points = min(10.0, len(fixing) / needed * 10)
    return round(points, 2), {"fixing_land_count": len(fixing), "color_count": color_count}


def score_strategy_execution(
    tagged: list[tuple[dict, set, bool]], tutor_weighted_count: float
) -> tuple[int, dict]:
    """Win Con (0-40) + Consistency (0-30) + Speed (0-30) -> 0-100 execution
    score, mapped to the published +0..+35 thresholds.

    Win-con scoring covers Extra Turns / Extra Combats / Overrun only - combo
    win conditions need Commander Spellbook integration (deferred).
    """
    extra_turn_count = _count_signal(tagged, "EXTRA_TURN")
    extra_combat_count = _count_signal(tagged, "EXTRA_COMBAT")
    overrun_count = _count_signal(tagged, "OVERRUN")
    creature_count = sum(
        1 for c, _, is_cmd in tagged
        if not is_cmd and "Creature" in (c.get("type_line") or "")
    )

    win_con_candidates = {
        "Extra Turns": min(40, extra_turn_count * 10),
        "Extra Combats": min(40, extra_combat_count * 8),
    }
    if creature_count >= 10:
        win_con_candidates["Overrun"] = min(40, overrun_count * 10)
    win_con_candidates = {k: v for k, v in win_con_candidates.items() if v > 0}

    if win_con_candidates:
        primary_label = max(win_con_candidates, key=win_con_candidates.get)
        primary_score = win_con_candidates.pop(primary_label)
        secondary_score = sum(win_con_candidates.values()) / 3
        win_con_score = min(40.0, primary_score + secondary_score)
    else:
        primary_label = None
        win_con_score = 0.0

    draw_count = _count_signal(tagged, "DRAW") + _count_signal(tagged, "IMPULSE_DRAW")
    consistency_index = min(100.0, tutor_weighted_count * 7 + min(10, draw_count))
    consistency_subscore = consistency_index / 100 * 30

    fast_mana_count = sum(
        1 for c, signals, _ in tagged if "FAST_MANA" in signals and c["name"] != "Sol Ring"
    )
    mana_rocks = [
        c for c, signals, _ in tagged
        if "RAMP" in signals and c["name"] not in data.FAST_MANA
        and "Creature" not in (c.get("type_line") or "")
        and "Land" not in (c.get("type_line") or "")
    ]
    ramp_dorks = [
        c for c, signals, _ in tagged
        if "RAMP" in signals and (
            "Creature" in (c.get("type_line") or "") or "Land" in (c.get("type_line") or "")
        )
    ]
    treasure_cards = [
        c for c, _, _ in tagged if data.TREASURE_RE.search(c.get("oracle_text") or "")
    ]

    nonland_cmcs = [
        c.get("cmc") or 0 for c, _, is_cmd in tagged
        if not is_cmd and "Land" not in (c.get("type_line") or "")
    ]
    avg_cmc = sum(nonland_cmcs) / len(nonland_cmcs) if nonland_cmcs else 0.0

    _, concentration = _theme_concentration(tagged)

    speed_index = (
        min(40, fast_mana_count * 5)
        + min(15, len(mana_rocks) * 3)
        + min(14, len(ramp_dorks) * 2)
        + min(10, len(treasure_cards) * 3)
        + _avg_cmc_score(avg_cmc)
        + min(30, extra_turn_count * 12)
        + min(25, extra_combat_count * 8)
        + (15 if concentration >= 50 else 0)
    )
    speed_index = min(100.0, speed_index)
    speed_subscore = speed_index / 100 * 30

    execution_score = win_con_score + consistency_subscore + speed_subscore
    points = _execution_points(execution_score)

    return points, {
        "execution_score": round(execution_score, 1),
        "win_con_score": round(win_con_score, 1),
        "win_con_label": primary_label,
        "consistency_index": round(consistency_index, 1),
        "speed_index": round(speed_index, 1),
        "avg_cmc": round(avg_cmc, 2),
        "estimated_win_turn": _estimated_win_turn(speed_index, consistency_index),
    }


def score_cohesion(tagged: list[tuple[dict, set, bool]]) -> tuple[int, dict]:
    dominant, concentration = _theme_concentration(tagged)
    density = _synergy_density(tagged)
    cohesion_score = concentration * 0.6 + density * 0.4

    if cohesion_score >= 75:
        points = 20
    elif cohesion_score >= 60:
        points = 14
    elif cohesion_score >= 45:
        points = 8
    elif cohesion_score >= 30:
        points = 3
    else:
        points = 0

    return points, {
        "dominant_theme": dominant,
        "concentration": round(concentration, 1),
        "density": round(density, 1),
        "cohesion_score": round(cohesion_score, 1),
    }


def score_backbone(tagged: list[tuple[dict, set, bool]], color_identity: list[str]) -> tuple[int, dict]:
    colors = set(color_identity or [])

    draw_count = _count_signal(tagged, "DRAW") + _count_signal(tagged, "IMPULSE_DRAW")
    ramp_count = _count_signal(tagged, "RAMP")
    removal_count = _count_signal(tagged, "REMOVAL")
    wipe_count = _count_signal(tagged, "WIPE")
    tutor_count = _count_signal(tagged, "TUTOR")
    counter_count = _count_signal(tagged, "COUNTERSPELL")
    recursion_count = _count_signal(tagged, "RECURSION")
    protection_count = _count_signal(tagged, "PROTECTION")

    counter_cap = 10 if "U" in colors else 4
    recursion_cap = 10 if colors & {"B", "G"} else 6
    protection_cap = 10 if colors & {"W", "G"} else 6

    components = {
        "draw": min(20, draw_count * 2),
        "ramp": min(20, ramp_count * 2),
        "removal": min(15, (removal_count + wipe_count * 1.5) * 1.5),
        "tutors": min(15, tutor_count * 3),
        "counterspells": min(counter_cap, counter_count * 3),
        "recursion": min(recursion_cap, recursion_count * 3),
        "protection": min(protection_cap, protection_count * 3),
    }
    max_total = 20 + 20 + 15 + 15 + counter_cap + recursion_cap + protection_cap
    backbone_index = sum(components.values()) / max_total * 100

    if backbone_index >= 75:
        points = 10
    elif backbone_index >= 55:
        points = 6
    elif backbone_index >= 35:
        points = 3
    elif backbone_index >= 15:
        points = 1
    else:
        points = 0

    return points, {
        "backbone_index": round(backbone_index, 1),
        "components": {k: round(v, 1) for k, v in components.items()},
    }


def calculate_power_level(
    commanders: list[dict], mainboard: list[dict], color_identity: list[str]
) -> dict:
    """Score a deck and map it to a Bracket (1-5) and Powerlevel (0-10)."""
    tagged = [(card, tag_card(card), True) for card in commanders]
    tagged += [(card, tag_card(card), False) for card in mainboard]

    gc_points, gc_detail = score_game_changers(tagged)
    tutor_points, tutor_detail = score_tutors(tagged)
    fast_mana_points, fast_mana_detail = score_fast_mana(tagged)
    mana_base_points, mana_base_detail = score_mana_base(tagged, color_identity)
    execution_points, execution_detail = score_strategy_execution(
        tagged, tutor_detail["weighted_count"]
    )
    cohesion_points, cohesion_detail = score_cohesion(tagged)
    backbone_points, backbone_detail = score_backbone(tagged, color_identity)

    score = round(
        min(
            100.0,
            gc_points
            + tutor_points
            + fast_mana_points
            + mana_base_points
            + execution_points
            + cohesion_points
            + backbone_points,
        ),
        2,
    )

    if score >= 96:
        bracket = 5
    elif score >= 71:
        bracket = 4
    elif score >= 36:
        bracket = 3
    elif score >= 11:
        bracket = 2
    else:
        bracket = 1

    # Hard gate: 4+ Game Changers guarantees at least Bracket 4. Gates can
    # only raise the bracket, never lower it.
    if gc_detail["count"] >= 4:
        bracket = max(bracket, 4)

    archetype = cohesion_detail["dominant_theme"] if cohesion_detail["concentration"] >= 30 else None

    return {
        "score": score,
        "bracket": bracket,
        "bracket_label": BRACKET_LABELS[bracket],
        "powerlevel": round(score / 10, 2),
        "archetype": archetype,
        "breakdown": {
            "game_changers": {"points": gc_points, **gc_detail},
            "tutors": {"points": tutor_points, **tutor_detail},
            "fast_mana": {"points": fast_mana_points, **fast_mana_detail},
            "mana_base": {"points": mana_base_points, **mana_base_detail},
            "strategy_execution": {"points": execution_points, **execution_detail},
            "cohesion": {"points": cohesion_points, **cohesion_detail},
            "backbone": {"points": backbone_points, **backbone_detail},
        },
    }
