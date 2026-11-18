"""Moves: "What does my Pokémon learn, and at what level?" """
import pytest


def level_up_moves(pokemon: dict, version_group: str) -> dict[str, int]:
    """{move name: level} for moves learned by level-up in one game (version group)."""
    learnset = {}
    for entry in pokemon["moves"]:
        for detail in entry["version_group_details"]:
            if (detail["version_group"]["name"] == version_group
                    and detail["move_learn_method"]["name"] == "level-up"):
                learnset[entry["move"]["name"]] = detail["level_learned_at"]
    return learnset


@pytest.mark.parametrize("version_group, level", [("red-blue", 42), ("scarlet-violet", 33)])
def test_squirtle_learns_hydro_pump_at_different_levels_per_game(api, version_group, level):
    learnset = level_up_moves(api.json("/pokemon/squirtle"), version_group)
    assert learnset["hydro-pump"] == level


def test_squirtle_red_blue_learnset(api):
    assert level_up_moves(api.json("/pokemon/squirtle"), "red-blue") == {
        "tackle": 1, "tail-whip": 1, "bubble": 8, "water-gun": 15,
        "bite": 22, "withdraw": 28, "skull-bash": 35, "hydro-pump": 42,
    }


@pytest.mark.parametrize("move, expected", [
    ("hydro-pump", {"power": 110, "accuracy": 80, "pp": 5, "priority": 0, "type": "water", "damage_class": "special"}),
    ("shadow-ball", {"power": 80, "accuracy": 100, "pp": 15, "priority": 0, "type": "ghost", "damage_class": "special"}),
])
def test_move_details(api, move, expected):
    data = api.json(f"/move/{move}")
    actual = {k: data[k] for k in ("power", "accuracy", "pp", "priority")}
    actual["type"] = data["type"]["name"]
    actual["damage_class"] = data["damage_class"]["name"]
    assert actual == expected


def test_move_history_records_older_power(api):
    # Hydro Pump was 120 power before Gen 6; the API stores the value before the X/Y change.
    past = api.json("/move/hydro-pump")["past_values"]
    assert {(p["version_group"]["name"], p["power"]) for p in past} == {("x-y", 120)}


@pytest.mark.parametrize("pokemon, move", [("gengar", "shadow-ball"), ("blastoise", "hydro-pump"),
                                           ("psyduck", "hydro-pump")])
def test_move_and_pokemon_agree_on_who_learns_it(api, pokemon, move):
    pokemon_moves = {m["move"]["name"] for m in api.json(f"/pokemon/{pokemon}")["moves"]}
    learners = {p["name"] for p in api.json(f"/move/{move}")["learned_by_pokemon"]}
    assert move in pokemon_moves
    assert pokemon in learners


def test_learn_levels_are_valid(api):
    for entry in api.json("/pokemon/dragonite")["moves"]:
        for detail in entry["version_group_details"]:
            level = detail["level_learned_at"]
            assert 0 <= level <= 100, f"{entry['move']['name']} at level {level}"
            if detail["move_learn_method"]["name"] != "level-up":
                assert level == 0, f"non-level-up move {entry['move']['name']} has level {level}"
