"""Reference data and oracle-text patterns for the power-level scoring engine.

The scoring formula and category definitions follow the methodology published
on commanderpowermeter.com's "How It Works" page (multi-factor 0-100 score,
mapped to the official WotC Commander Brackets 1-5).
"""

import re

# Official WotC "Game Changers" list (per Scryfall's `is:gamechanger`).
# Used for the Game Changer score factor and the Bracket 4 hard gate.
GAME_CHANGERS = {
    "Ad Nauseam",
    "Ancient Tomb",
    "Aura Shards",
    "Biorhythm",
    "Bolas's Citadel",
    "Braids, Cabal Minion",
    "Chrome Mox",
    "Coalition Victory",
    "Consecrated Sphinx",
    "Crop Rotation",
    "Cyclonic Rift",
    "Demonic Tutor",
    "Drannith Magistrate",
    "Enlightened Tutor",
    "Farewell",
    "Field of the Dead",
    "Fierce Guardianship",
    "Force of Will",
    "Gaea's Cradle",
    "Gamble",
    "Gifts Ungiven",
    "Glacial Chasm",
    "Grand Arbiter Augustin IV",
    "Grim Monolith",
    "Humility",
    "Imperial Seal",
    "Intuition",
    "Jeska's Will",
    "Lion's Eye Diamond",
    "Mana Vault",
    "Mishra's Workshop",
    "Mox Diamond",
    "Mystical Tutor",
    "Narset, Parter of Veils",
    "Natural Order",
    "Necropotence",
    "Notion Thief",
    "Opposition Agent",
    "Orcish Bowmasters",
    "Panoptic Mirror",
    "Rhystic Study",
    "Seedborn Muse",
    "Serra's Sanctum",
    "Smothering Tithe",
    "Survival of the Fittest",
    "Teferi's Protection",
    "Tergrid, God of Fright // Tergrid's Lantern",
    "Thassa's Oracle",
    "The One Ring",
    "The Tabernacle at Pendrell Vale",
    "Underworld Breach",
    "Vampiric Tutor",
    "Worldly Tutor",
}

# Elite fast-mana: 0-cost-equivalent acceleration that nets mana far ahead of
# curve. Sol Ring is included for tagging but excluded from the *count* used
# in scoring, per the published "Sol Ring excluded as universal baseline" rule.
FAST_MANA = {
    "Black Lotus",
    "Mox Pearl",
    "Mox Sapphire",
    "Mox Jet",
    "Mox Ruby",
    "Mox Emerald",
    "Mox Diamond",
    "Mox Opal",
    "Chrome Mox",
    "Lotus Petal",
    "Jeweled Lotus",
    "Lion's Eye Diamond",
    "Mana Crypt",
    "Mana Vault",
    "Grim Monolith",
    "Basalt Monolith",
    "Sol Ring",
    "Ancient Tomb",
    "City of Traitors",
    "Mishra's Workshop",
    "Dark Ritual",
    "Cabal Ritual",
    "Seething Song",
    "Culling the Weak",
    "Jeska's Will",
    "Channel",
    "Simian Spirit Guide",
    "Elvish Spirit Guide",
}

_F = re.IGNORECASE

# --- Tutor scope/recognition -------------------------------------------------
TUTOR_RE = re.compile(r"search(?:es)? (?:your|their) library for", _F)
LAND_TUTOR_RE = re.compile(r"search(?:es)? (?:your|their) library for .{0,40}land card", _F)
TUTOR_BROAD_RE = re.compile(r"search(?:es)? (?:your|their) library for a card", _F)

# --- Ramp ---------------------------------------------------------------------
MANA_ABILITY_RE = re.compile(r"\{T\}[^.]*?:\s*add\b", _F)
TREASURE_RE = re.compile(r"creates? .{0,30}treasure token", _F)

# --- Mana base (fixing lands) ---------------------------------------------------
FIXING_LAND_RE = re.compile(
    r"add (?:one mana of any color|\{[wubrg]\}\{[wubrg]\}|two mana of (?:any one color|different colors))",
    _F,
)

# --- Removal / interaction -----------------------------------------------------
REMOVAL_RE = re.compile(
    r"(?:destroy|exile) target (?:creature|artifact|enchantment|planeswalker|permanent|land)",
    _F,
)
WIPE_RE = re.compile(
    r"(?:destroy|exile) all (?:creatures|permanents|artifacts|enchantments)"
    r"|each (?:creature|player|opponent) sacrifices"
    r"|all creatures (?:get|have)",
    _F,
)
COUNTERSPELL_RE = re.compile(r"counter target spell", _F)
RECURSION_RE = re.compile(
    r"return target .{0,60}from (?:your |a |target player's |their )?graveyard"
    r" to (?:your hand|the battlefield|its owner's hand)",
    _F,
)
PROTECTION_RE = re.compile(r"\b(?:hexproof|indestructible|protection from|shroud)\b", _F)

# --- Card advantage / speed -----------------------------------------------------
DRAW_RE = re.compile(r"draws? (?:a|an|x|\d+|two|three|four|five|six|seven) cards?", _F)
LOOT_RE = re.compile(r"draws? a card,?\s*(?:then|and)\s*discards?", _F)
IMPULSE_DRAW_RE = re.compile(r"exile the top card.{0,60}you may play", _F)

# --- Win conditions ---------------------------------------------------------------
EXTRA_TURN_RE = re.compile(r"take an extra turn", _F)
EXTRA_COMBAT_RE = re.compile(r"(?:additional|extra|another) combat phase", _F)
OVERRUN_RE = re.compile(r"creatures you control get \+(?:[3-9]|\d{2,})/\+\d+", _F)

# --- Other signal categories ------------------------------------------------------
STAX_RE = re.compile(
    r"can't (?:cast|attack|block|untap)"
    r"|spells cost \{1\} more"
    r"|players can't draw"
    r"|skip your",
    _F,
)
INFECT_RE = re.compile(r"\b(?:infect|wither)\b|poison counter", _F)
THEFT_RE = re.compile(
    r"gain control of target"
    r"|cast (?:it|that spell) without paying its mana cost"
    r"|search .{0,40}(?:opponent|another player)(?:'s)? (?:hand|library)",
    _F,
)
BURN_RE = re.compile(r"deals? \d+ damage to (?:any target|each opponent|target player|target opponent)", _F)
TEMPO_RE = re.compile(r"return target .{0,40}to (?:its|their) owner's hand|phases? out", _F)
CHAOS_RE = re.compile(r"flip a coin|roll a (?:d\d+|die)", _F)

# --- Engine / theme keyword groups (for cohesion + archetype suggestion) ----------
ENGINE_THEMES = {
    "Graveyard": re.compile(r"graveyard", _F),
    "Aristocrats": re.compile(r"sacrifice (?:a|another) creature|whenever .{0,30}creature .{0,15}dies", _F),
    "Tokens": re.compile(r"creates? .{0,30}tokens?", _F),
    "Spellslinger": re.compile(r"instant or sorcery spell|whenever you cast an instant or a sorcery|magecraft", _F),
    "Landfall": re.compile(r"landfall|whenever a land enters the battlefield under your control", _F),
    "Lands Matter": re.compile(r"additional land|extra land|land card from your hand", _F),
    "Wheel": re.compile(r"each player draws .{0,20}cards? and discards|discards? (?:their|its) hand", _F),
    "Artifacts": re.compile(r"artifact you control|whenever an artifact enters|metalcraft", _F),
    "Voltron": re.compile(r"\bequip\b|aura you control|equipped creature|enchant creature", _F),
}
