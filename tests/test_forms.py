"""Alternate forms: Megas, Gigantamax, and Pokémon with more than one form."""
import jsonschema
import pytest

from tests import schemas
from tests.helpers import base_stat_total, stat_map, type_names


@pytest.mark.parametrize("bare_name, default_form", [("giratina", "giratina-altered"),
                                                     ("aegislash", "aegislash-shield")])
def test_multi_form_pokemon_need_form_name(api, bare_name, default_form):
    """Gotcha for players: /pokemon/giratina 404s, because the record is stored under its form name.

    The species endpoint does accept the bare name, and its default variety leads to the right record.
    """
    resp = api.get(f"/pokemon/{bare_name}")
    assert resp.status_code == 404
    jsonschema.validate(resp.json(), schemas.NOT_FOUND)

    species = api.json(f"/pokemon-species/{bare_name}")
    default = [v["pokemon"] for v in species["varieties"] if v["is_default"]]
    assert [d["name"] for d in default] == [default_form]
    assert api.json(default[0]["url"])["name"] == default_form


def test_aegislash_blade_swaps_offense_and_defense(api):
    shield = stat_map(api.json("/pokemon/aegislash-shield"))
    blade = stat_map(api.json("/pokemon/aegislash-blade"))
    assert (blade["attack"], blade["defense"]) == (shield["defense"], shield["attack"]) == (140, 50)
    assert (blade["special-attack"], blade["special-defense"]) == (shield["special-defense"], shield["special-attack"])
    assert blade["hp"] == shield["hp"] and blade["speed"] == shield["speed"]
    assert sum(blade.values()) == sum(shield.values()) == 500


def test_giratina_origin_form(api):
    altered = api.json("/pokemon/giratina-altered")
    origin = api.json("/pokemon/giratina-origin")
    assert type_names(origin) == type_names(altered) == ["ghost", "dragon"]
    assert base_stat_total(origin) == base_stat_total(altered) == 680
    assert [a["ability"]["name"] for a in origin["abilities"]] == ["levitate"]
    assert stat_map(origin)["attack"] == 120 and stat_map(altered)["attack"] == 100


@pytest.mark.parametrize("base, mega, mega_bst, mega_ability", [
    ("blastoise", "blastoise-mega", 630, "mega-launcher"),
    ("gengar", "gengar-mega", 600, "shadow-tag"),
    ("dragonite", "dragonite-mega", 700, "multiscale"),
])
def test_mega_evolution(api, base, mega, mega_bst, mega_ability):
    base_pokemon = api.json(f"/pokemon/{base}")
    mega_pokemon = api.json(f"/pokemon/{mega}")

    assert base_stat_total(mega_pokemon) == mega_bst == base_stat_total(base_pokemon) + 100
    assert mega_pokemon["is_default"] is False
    assert [a["ability"]["name"] for a in mega_pokemon["abilities"]] == [mega_ability]

    form = api.json(f"/pokemon-form/{mega}")
    assert form["is_mega"] is True
    assert form["is_battle_only"] is True


def test_gigantamax_keeps_base_stats(api):
    gmax = api.json("/pokemon/gengar-gmax")
    assert stat_map(gmax) == stat_map(api.json("/pokemon/gengar"))
    form = api.json("/pokemon-form/gengar-gmax")
    assert form["is_mega"] is False and form["form_name"] == "gmax"


@pytest.mark.parametrize("species", ["blastoise", "giratina", "dragonite", "aegislash", "gengar"])
def test_every_variety_link_resolves(api, species):
    varieties = api.json(f"/pokemon-species/{species}")["varieties"]
    assert sum(v["is_default"] for v in varieties) == 1
    for v in varieties:
        pokemon = api.json(v["pokemon"]["url"])
        assert pokemon["name"] == v["pokemon"]["name"]
        assert pokemon["species"]["name"] == species
        assert pokemon["is_default"] is v["is_default"]
