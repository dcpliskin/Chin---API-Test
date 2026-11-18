"""Expected values for the test Pokémon, all observed from the live API on 2026-11-18.

Only long-stable game data is pinned here (Pokédex numbers, types, base stats,
evolution methods). Values that grow over time (total counts, learnsets in new
games) are checked by consistency rules in the tests instead.
"""

# Default /pokemon/{name} records.
POKEMON = {
    "squirtle": {
        "id": 7, "types": ["water"],
        "stats": {"hp": 44, "attack": 48, "defense": 65, "special-attack": 50, "special-defense": 64, "speed": 43},
        "bst": 314, "abilities": ["torrent"], "hidden_ability": "rain-dish",
    },
    "blastoise": {
        "id": 9, "types": ["water"],
        "stats": {"hp": 79, "attack": 83, "defense": 100, "special-attack": 85, "special-defense": 105, "speed": 78},
        "bst": 530, "abilities": ["torrent"], "hidden_ability": "rain-dish",
    },
    "psyduck": {
        "id": 54, "types": ["water"],
        "stats": {"hp": 50, "attack": 52, "defense": 48, "special-attack": 65, "special-defense": 50, "speed": 55},
        "bst": 320, "abilities": ["damp", "cloud-nine"], "hidden_ability": "swift-swim",
    },
    "gengar": {
        "id": 94, "types": ["ghost", "poison"],
        "stats": {"hp": 60, "attack": 65, "defense": 60, "special-attack": 130, "special-defense": 75, "speed": 110},
        "bst": 500, "abilities": ["cursed-body"], "hidden_ability": None,
    },
    "dragonite": {
        "id": 149, "types": ["dragon", "flying"],
        "stats": {"hp": 91, "attack": 134, "defense": 95, "special-attack": 100, "special-defense": 100, "speed": 80},
        "bst": 600, "abilities": ["inner-focus"], "hidden_ability": "multiscale",
    },
    "skitty": {
        "id": 300, "types": ["normal"],
        "stats": {"hp": 50, "attack": 45, "defense": 45, "special-attack": 35, "special-defense": 35, "speed": 50},
        "bst": 260, "abilities": ["cute-charm", "normalize"], "hidden_ability": "wonder-skin",
    },
    "torterra": {
        "id": 389, "types": ["grass", "ground"],
        "stats": {"hp": 95, "attack": 109, "defense": 105, "special-attack": 75, "special-defense": 85, "speed": 56},
        "bst": 525, "abilities": ["overgrow"], "hidden_ability": "shell-armor",
    },
    "giratina-altered": {
        "id": 487, "types": ["ghost", "dragon"],
        "stats": {"hp": 150, "attack": 100, "defense": 120, "special-attack": 100, "special-defense": 120, "speed": 90},
        "bst": 680, "abilities": ["pressure"], "hidden_ability": "telepathy",
    },
    "aegislash-shield": {
        "id": 681, "types": ["steel", "ghost"],
        "stats": {"hp": 60, "attack": 50, "defense": 140, "special-attack": 50, "special-defense": 140, "speed": 60},
        "bst": 500, "abilities": ["stance-change"], "hidden_ability": None,
    },
}

# /pokemon-species/{name} records.
SPECIES = {
    "squirtle":  {"generation": "generation-i",   "genus": "Tiny Turtle Pokémon", "legendary": False, "egg_groups": {"monster", "water1"}},
    "blastoise": {"generation": "generation-i",   "genus": "Shellfish Pokémon",   "legendary": False, "egg_groups": {"monster", "water1"}},
    "psyduck":   {"generation": "generation-i",   "genus": "Duck Pokémon",        "legendary": False, "egg_groups": {"water1", "ground"}},
    "gengar":    {"generation": "generation-i",   "genus": "Shadow Pokémon",      "legendary": False, "egg_groups": {"indeterminate"}},
    "dragonite": {"generation": "generation-i",   "genus": "Dragon Pokémon",      "legendary": False, "egg_groups": {"water1", "dragon"}},
    "skitty":    {"generation": "generation-iii", "genus": "Kitten Pokémon",      "legendary": False, "egg_groups": {"ground", "fairy"}},
    "torterra":  {"generation": "generation-iv",  "genus": "Continent Pokémon",   "legendary": False, "egg_groups": {"monster", "plant"}},
    "giratina":  {"generation": "generation-iv",  "genus": "Renegade Pokémon",    "legendary": True,  "egg_groups": {"no-eggs"}},
    "aegislash": {"generation": "generation-vi",  "genus": "Royal Sword Pokémon", "legendary": False, "egg_groups": {"mineral"}},
}

# Type matchups a player would look up: {pokemon: {multiplier: {attacking types}}}.
# Only notable multipliers are listed; each listed set must match exactly.
MATCHUPS = {
    "dragonite": {4.0: {"ice"}, 0.25: {"grass"}, 0.0: {"ground"}},
    "torterra": {4.0: {"ice"}, 0.0: {"electric"}},
    "gengar": {0.25: {"poison", "bug"}, 0.0: {"normal", "fighting"}},
    "aegislash-shield": {0.25: {"bug"}, 0.0: {"normal", "fighting", "poison"}},
    "giratina-altered": {2.0: {"ghost", "ice", "dragon", "dark", "fairy"}, 0.0: {"normal", "fighting"}},
    "skitty": {2.0: {"fighting"}, 0.0: {"ghost"}},
    "squirtle": {2.0: {"grass", "electric"}, 0.5: {"steel", "fire", "water", "ice"}},
}

# Evolution steps: (from, to, trigger, detail key, detail value), using the earliest (default) method.
EVOLUTIONS = [
    ("squirtle", "wartortle", "level-up", "min_level", 16),
    ("wartortle", "blastoise", "level-up", "min_level", 36),
    ("dratini", "dragonair", "level-up", "min_level", 30),
    ("dragonair", "dragonite", "level-up", "min_level", 55),
    ("turtwig", "grotle", "level-up", "min_level", 18),
    ("grotle", "torterra", "level-up", "min_level", 32),
    ("psyduck", "golduck", "level-up", "min_level", 33),
    ("skitty", "delcatty", "use-item", "item", "moon-stone"),
    ("doublade", "aegislash", "use-item", "item", "dusk-stone"),
    ("haunter", "gengar", "trade", None, None),
]
