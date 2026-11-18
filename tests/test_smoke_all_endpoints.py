"""Smoke test of every resource the API exposes: each list is valid, and its first item can be fetched.

This gives breadth across all doc sections (Berries, Contests, Items, Machines, ...).
The deeper player-focused checks live in the other modules.
"""
import jsonschema
import pytest

from tests import schemas

# Observed from GET /api/v2/ on 2026-11-18. The docs say these 5 return unnamed lists ({url} only).
UNNAMED = {"characteristic", "contest-effect", "evolution-chain", "machine", "super-contest-effect"}
NAMED = {
    "ability", "berry", "berry-firmness", "berry-flavor", "contest-type", "currency", "egg-group",
    "encounter-condition", "encounter-condition-value", "encounter-method", "evolution-trigger",
    "evolution-variable", "gender", "generation", "growth-rate", "item", "item-attribute", "item-category",
    "item-fling-effect", "item-pocket", "language", "location", "location-area", "move", "move-ailment",
    "move-battle-style", "move-category", "move-damage-class", "move-learn-method", "move-target", "nature",
    "pal-park-area", "pokeathlon-stat", "pokedex", "pokemon", "pokemon-color", "pokemon-form",
    "pokemon-habitat", "pokemon-shape", "pokemon-species", "region", "stat", "type", "version", "version-group",
}
NOT_A_LIST = {"meta"}  # deploy information, not a resource list

UNNAMED_PAGE = {**schemas.PAGE, "properties": {**schemas.PAGE["properties"], "results": {
    "type": "array", "items": {"type": "object", "required": ["url"]}}}}


def test_root_lists_every_known_endpoint(api):
    """Fails if an endpoint is added or removed, so this file gets updated."""
    root = api.json("/")
    assert set(root) == NAMED | UNNAMED | NOT_A_LIST
    for name, url in root.items():
        assert url == f"https://pokeapi.co/api/v2/{name}/"


@pytest.mark.parametrize("endpoint", sorted(NAMED | UNNAMED))
def test_list_is_valid_and_first_item_resolves(api, endpoint):
    page = api.json(f"/{endpoint}", limit=1)
    jsonschema.validate(page, schemas.PAGE if endpoint in NAMED else UNNAMED_PAGE)
    assert page["count"] >= 1
    assert len(page["results"]) == 1

    first = page["results"][0]
    item = api.json(first["url"])
    assert item["id"] == int(first["url"].rstrip("/").split("/")[-1])  # the link leads to the record it names
    if endpoint in NAMED:
        assert item["name"] == first["name"]


def test_meta_reports_deployment(api):
    meta = api.json("/meta")
    assert set(meta) >= {"deploy_date", "hash"}
    assert len(meta["hash"]) == 40  # a git commit SHA
