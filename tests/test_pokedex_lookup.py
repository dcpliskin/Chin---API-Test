"""Looking up a Pokémon: the basic Pokédex entry a player searches for."""
import jsonschema
import pytest

from tests import schemas
from tests.data.favorites import POKEMON, SPECIES
from tests.helpers import base_stat_total, names, stat_map, type_names


@pytest.mark.parametrize("name", POKEMON)
def test_lookup_by_name_and_id_return_same_pokemon(api, name):
    by_name = api.json(f"/pokemon/{name}")
    by_id = api.json(f"/pokemon/{POKEMON[name]['id']}")
    assert by_name == by_id
    assert by_name["name"] == name


@pytest.mark.parametrize("name", POKEMON)
def test_pokemon_matches_schema(api, name):
    jsonschema.validate(api.json(f"/pokemon/{name}"), schemas.POKEMON)


@pytest.mark.parametrize("name", POKEMON)
def test_types(api, name):
    assert type_names(api.json(f"/pokemon/{name}")) == POKEMON[name]["types"]


@pytest.mark.parametrize("name", POKEMON)
def test_base_stats_and_total(api, name):
    pokemon = api.json(f"/pokemon/{name}")
    assert stat_map(pokemon) == POKEMON[name]["stats"]
    assert base_stat_total(pokemon) == POKEMON[name]["bst"]


@pytest.mark.parametrize("name", POKEMON)
def test_regular_and_hidden_abilities(api, name):
    abilities = api.json(f"/pokemon/{name}")["abilities"]
    regular = [a["ability"]["name"] for a in sorted(abilities, key=lambda a: a["slot"]) if not a["is_hidden"]]
    hidden = [a["ability"]["name"] for a in abilities if a["is_hidden"]]

    assert regular == POKEMON[name]["abilities"]
    expected_hidden = POKEMON[name]["hidden_ability"]
    assert hidden == ([expected_hidden] if expected_hidden else [])


@pytest.mark.parametrize("name", SPECIES)
def test_species_entry(api, name):
    species = api.json(f"/pokemon-species/{name}")
    jsonschema.validate(species, schemas.SPECIES)
    expected = SPECIES[name]

    assert species["generation"]["name"] == expected["generation"]
    assert species["is_legendary"] is expected["legendary"]
    assert species["is_mythical"] is False
    assert names(species["egg_groups"]) == expected["egg_groups"]
    english_genus = [g["genus"] for g in species["genera"] if g["language"]["name"] == "en"]
    assert english_genus == [expected["genus"]]


@pytest.mark.parametrize("query", ["GENGAR", "Gengar", "gEnGaR"])
def test_name_lookup_is_case_insensitive(api, query):
    # Players type names with capitals. Observed: the API normalizes them (not stated in the docs).
    assert api.json(f"/pokemon/{query}")["id"] == POKEMON["gengar"]["id"]


def test_trailing_slash_is_accepted(api):
    assert api.json("/pokemon/gengar/")["id"] == POKEMON["gengar"]["id"]


def test_species_and_pokemon_link_to_each_other(api):
    gengar = api.json("/pokemon/gengar")
    species = api.json(gengar["species"]["url"])
    assert species["name"] == "gengar"
    default_variety = [v["pokemon"]["name"] for v in species["varieties"] if v["is_default"]]
    assert default_variety == ["gengar"]
