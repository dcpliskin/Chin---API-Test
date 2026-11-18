"""Type matchups: "What is my Pokémon weak or immune to?"

Multipliers are computed the way a player's damage calculator would: by combining
the /type/{name} damage_relations of each of the Pokémon's types.
"""
import pytest

from tests.data.favorites import MATCHUPS
from tests.helpers import damage_multiplier, names, type_names

# The 18 battle types. The API also lists 'unknown', 'shadow' (spin-off games), and 'stellar' (Tera-only),
# which no Pokémon has as a normal type.
BATTLE_TYPES = [
    "normal", "fighting", "flying", "poison", "ground", "rock", "bug", "ghost", "steel",
    "fire", "water", "grass", "electric", "psychic", "ice", "dragon", "dark", "fairy",
]


@pytest.fixture(scope="module")
def type_chart(api):
    return {t: api.json(f"/type/{t}") for t in BATTLE_TYPES}


def test_type_list_contains_all_battle_types(api):
    listed = names(api.json("/type", limit=100)["results"])
    assert set(BATTLE_TYPES) <= listed


@pytest.mark.parametrize("pokemon", MATCHUPS)
def test_notable_weaknesses_and_resistances(api, type_chart, pokemon):
    defending = {t: type_chart[t] for t in type_names(api.json(f"/pokemon/{pokemon}"))}
    actual: dict[float, set[str]] = {}
    for attacker in BATTLE_TYPES:
        actual.setdefault(damage_multiplier(attacker, defending), set()).add(attacker)

    for multiplier, expected_types in MATCHUPS[pokemon].items():
        assert actual.get(multiplier, set()) == expected_types, f"{pokemon} x{multiplier}"


def test_type_chart_is_symmetric(type_chart):
    """If A deals double/half/no damage to B, then B must take double/half/no damage from A."""
    pairs = [("double_damage_to", "double_damage_from"),
             ("half_damage_to", "half_damage_from"),
             ("no_damage_to", "no_damage_from")]
    violations = []
    for a in BATTLE_TYPES:
        for b in BATTLE_TYPES:
            for to_key, from_key in pairs:
                a_says = b in names(type_chart[a]["damage_relations"][to_key])
                b_says = a in names(type_chart[b]["damage_relations"][from_key])
                if a_says != b_says:
                    violations.append(f"{a} {to_key} {b}")
    assert violations == []


def test_type_lists_its_pokemon(api):
    # Reverse lookup: "show me every Ghost type" should include Gengar.
    ghost = api.json("/type/ghost")
    assert {"gengar", "giratina-altered", "aegislash-shield"} <= names(p["pokemon"] for p in ghost["pokemon"])
