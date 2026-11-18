"""Evolution: "When or how does my Pokémon evolve?" """
import pytest

from tests.data.favorites import EVOLUTIONS
from tests.helpers import chain_species, default_evolution_detail, find_chain_link


def chain_for(api, species_name: str) -> dict:
    species = api.json(f"/pokemon-species/{species_name}")
    return api.json(species["evolution_chain"]["url"])["chain"]


@pytest.mark.parametrize("from_species, to_species, trigger, key, value", EVOLUTIONS,
                         ids=[f"{f}->{t}" for f, t, *_ in EVOLUTIONS])
def test_evolution_method(api, from_species, to_species, trigger, key, value):
    chain = chain_for(api, to_species)
    parent = find_chain_link(chain, from_species)
    assert parent, f"{from_species} not in {to_species}'s chain"
    child = next((c for c in parent["evolves_to"] if c["species"]["name"] == to_species), None)
    assert child, f"{from_species} does not evolve into {to_species}"

    detail = default_evolution_detail(child)
    assert detail["trigger"]["name"] == trigger
    if key == "item":
        assert detail["item"]["name"] == value
    elif key:
        assert detail[key] == value


def test_full_squirtle_line(api):
    assert chain_species(chain_for(api, "blastoise")) == ["squirtle", "wartortle", "blastoise"]


def test_gengar_also_evolves_with_linking_cord_in_legends_arceus(api):
    # Legends: Arceus has no trading, so trade evolutions use the Linking Cord item there instead.
    gengar = find_chain_link(chain_for(api, "gengar"), "gengar")
    methods = {(d["trigger"]["name"], (d.get("item") or {}).get("name")) for d in gengar["evolution_details"]}
    assert ("trade", None) in methods
    assert ("use-item", "linking-cord") in methods


def test_giratina_does_not_evolve(api):
    chain = chain_for(api, "giratina")
    assert chain["species"]["name"] == "giratina"
    assert chain["evolves_to"] == []
    assert api.json("/pokemon-species/giratina")["evolves_from_species"] is None


@pytest.mark.parametrize("species", ["blastoise", "dragonite", "torterra", "aegislash", "gengar"])
def test_evolves_from_species_agrees_with_chain(api, species):
    """The species' 'evolves_from' must be its parent in the evolution chain."""
    data = api.json(f"/pokemon-species/{species}")
    chain = api.json(data["evolution_chain"]["url"])["chain"]
    parent = data["evolves_from_species"]["name"]
    parent_link = find_chain_link(chain, parent)
    assert species in [c["species"]["name"] for c in parent_link["evolves_to"]]
