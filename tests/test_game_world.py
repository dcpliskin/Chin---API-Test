"""The game world around a Pokémon: items, TMs (machines), regional Pokédexes, locations, and games."""
import pytest

from tests.helpers import names

# --- Items -----------------------------------------------------------------


@pytest.mark.parametrize("item, evolves", [("moon-stone", "Skitty into Delcatty"), ("dusk-stone", None)])
def test_evolution_stones_are_evolution_items(api, item, evolves):
    data = api.json(f"/item/{item}")
    assert data["category"]["name"] == "evolution"
    if evolves:
        effect = [e["short_effect"] for e in data["effect_entries"] if e["language"]["name"] == "en"]
        assert any(evolves in text for text in effect)


def test_evolution_item_link_resolves_to_item(api):
    """Follow the link in Skitty's evolution details to the item record, as a player app would."""
    chain = api.json(api.json("/pokemon-species/skitty")["evolution_chain"]["url"])["chain"]
    item_link = chain["evolves_to"][0]["evolution_details"][0]["item"]
    assert api.json(item_link["url"])["name"] == "moon-stone"


def test_evolution_item_category_lists_our_items(api):
    items = names(api.json("/item-category/evolution")["items"])
    assert {"moon-stone", "dusk-stone", "linking-cord"} <= items


# --- Machines (TMs) ---------------------------------------------------------------


@pytest.mark.parametrize("version_group, tm", [("platinum", "tm30"), ("scarlet-violet", "tm114")])
def test_which_tm_teaches_shadow_ball(api, version_group, tm):
    machines = api.json("/move/shadow-ball")["machines"]
    match = [m for m in machines if m["version_group"]["name"] == version_group]
    assert len(match) == 1
    machine = api.json(match[0]["machine"]["url"])
    assert machine["item"]["name"] == tm
    assert machine["move"]["name"] == "shadow-ball"


def test_same_tm_number_teaches_different_moves_in_different_games(api):
    """TM numbers are per game: TM30 teaches Shadow Ball in Platinum but a different move in Red/Blue."""
    tm30 = {m["version_group"]["name"]: m["machine"]["url"] for m in api.json("/item/tm30")["machines"]}
    assert api.json(tm30["platinum"])["move"]["name"] == "shadow-ball"
    assert api.json(tm30["red-blue"])["move"]["name"] != "shadow-ball"


# --- Pokédexes ----------------------------------------------------------------------

@pytest.mark.parametrize("dex, species, number", [
    ("national", "torterra", 389), ("national", "aegislash", 681),
    ("kanto", "squirtle", 7), ("kanto", "dragonite", 149),
    ("original-sinnoh", "turtwig", 1), ("original-sinnoh", "torterra", 3), ("original-sinnoh", "gengar", 71),
    ("extended-sinnoh", "giratina", 210),  # Platinum's expanded dex ends with Giratina
])
def test_regional_dex_number(api, dex, species, number):
    entries = {e["pokemon_species"]["name"]: e["entry_number"] for e in api.json(f"/pokedex/{dex}")["pokemon_entries"]}
    assert entries[species] == number


def test_giratina_only_joins_the_sinnoh_dex_in_platinum(api):
    original = {e["pokemon_species"]["name"] for e in api.json("/pokedex/original-sinnoh")["pokemon_entries"]}
    extended = {e["pokemon_species"]["name"] for e in api.json("/pokedex/extended-sinnoh")["pokemon_entries"]}
    assert "giratina" not in original
    assert "giratina" in extended
    assert original <= extended  # Platinum's dex is a superset of Diamond/Pearl's


def test_national_dex_covers_every_species(api):
    national = api.json("/pokedex/national")["pokemon_entries"]
    species_count = api.json("/pokemon-species", limit=1)["count"]
    assert [e["entry_number"] for e in national] == list(range(1, species_count + 1))


# --- Locations and regions --------------------------------------------------------------

def test_location_area_lists_its_pokemon(api):
    """Reverse of 'where can I catch Giratina?': what can be caught in the Distortion World?"""
    area = api.json("/location-area/distortion-world-area")
    found = {p["pokemon"]["name"]: names(v["version"] for v in p["version_details"])
             for p in area["pokemon_encounters"]}
    assert found == {"giratina-altered": {"platinum"}}
    assert area["location"]["name"] == "distortion-world"


def test_location_belongs_to_region(api):
    location = api.json("/location/distortion-world")
    assert location["region"]["name"] == "sinnoh"
    region = api.json("/region/sinnoh")
    assert "distortion-world" in names(region["locations"])
    assert {"original-sinnoh", "extended-sinnoh"} <= names(region["pokedexes"])  # a future Sinnoh game may add one


# --- Games: generations, version groups, versions ----------------------------------------

def test_version_belongs_to_version_group_and_generation(api):
    version = api.json("/version/platinum")
    group = api.json(version["version_group"]["url"])
    assert group["generation"]["name"] == "generation-iv"
    assert names(group["pokedexes"]) == {"extended-sinnoh"}
    assert names(group["regions"]) == {"sinnoh"}


def test_generation_lists_its_new_species(api):
    gen4 = api.json("/generation/generation-iv")
    species = names(gen4["pokemon_species"])
    assert {"turtwig", "grotle", "torterra", "giratina"} <= species
    assert "gengar" not in species  # Gengar is Gen I
    assert gen4["main_region"]["name"] == "sinnoh"
