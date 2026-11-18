"""General API behavior: counts, pagination, errors, HTTP methods, and headers."""
import time

import jsonschema
import pytest

from tests import schemas
from tests.helpers import BASE_URL, TIMEOUT

BASE_SPECIES_COUNT = 1025  # National Dex through Gen 9 (Pecharunt). Pinned because it only changes with a new generation.


# --- Counts ---------------------------------------------------------------

def test_species_count_matches_national_dex(api):
    assert api.json("/pokemon-species", limit=1)["count"] == BASE_SPECIES_COUNT


def test_every_listed_pokemon_is_returned_and_unique(api):
    """`count` must equal the number of entries when walking every page (no gaps, no duplicates)."""
    first = api.json("/pokemon", limit=200)
    seen, page = [], first
    while True:
        jsonschema.validate(page, schemas.PAGE)
        seen += [p["name"] for p in page["results"]]
        if not page["next"]:
            break
        page = api.json(page["next"])
    assert len(seen) == first["count"]
    assert len(set(seen)) == len(seen)


def test_base_pokemon_ids_are_contiguous_and_forms_come_after(api):
    listing = api.json("/pokemon", limit=first_count(api))["results"]
    ids = [int(p["url"].rstrip("/").split("/")[-1]) for p in listing]
    base = [i for i in ids if i < 10000]
    forms = [i for i in ids if i >= 10000]

    assert base == list(range(1, BASE_SPECIES_COUNT + 1))
    assert forms and min(forms) == 10001  # alternate forms (megas, regional forms, ...) start at 10001
    assert len(ids) == len(base) + len(forms)


def first_count(api) -> int:
    return api.json("/pokemon", limit=1)["count"]


# --- Pagination -------------------------------------------------------------

def test_default_page_size_is_20(api):
    page = api.json("/pokemon")
    assert len(page["results"]) == 20
    assert page["previous"] is None
    assert "offset=20" in page["next"] and "limit=20" in page["next"]


def test_limit_and_offset_select_the_right_slice(api):
    page = api.json("/pokemon", limit=3, offset=6)  # Pokédex #7, #8, #9
    assert [p["name"] for p in page["results"]] == ["squirtle", "wartortle", "blastoise"]
    assert "offset=3" in page["previous"]
    assert "offset=9" in page["next"]


def test_offset_past_the_end_returns_empty_page(api):
    page = api.json("/pokemon", limit=5, offset=100000)
    assert page["results"] == []
    assert page["next"] is None


@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: limit=-1 returns count-1 results (last entry silently dropped)")
def test_negative_limit_does_not_drop_results(api):
    page = api.json("/pokemon", limit=-1)
    assert len(page["results"]) in (0, page["count"]), "expected either a rejection or the full list"


@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: negative offset wraps around to the end of the list")
def test_negative_offset_is_not_treated_as_from_the_end(api):
    page = api.json("/pokemon", limit=3, offset=-5)
    assert page["results"] == [] or page["results"][0]["name"] == "bulbasaur"


# --- Errors -----------------------------------------------------------------

@pytest.mark.parametrize("bad", ["0", "-1", "99999", "notapokemon", "pikachuu"])
def test_unknown_pokemon_returns_json_404(api, bad):
    resp = api.get(f"/pokemon/{bad}")
    assert resp.status_code == 404
    assert resp.headers["Content-Type"].startswith("application/json")
    jsonschema.validate(resp.json(), schemas.NOT_FOUND)


@pytest.mark.parametrize("blocked", ["farfetch'd", "mr.mime"])
def test_names_with_blocked_symbols_are_rejected(api, blocked):
    # The docs say URLs containing . , * % ; : ' ! @ + [ are blocked at the edge (Cloudflare) -> 403 HTML.
    resp = api.get(f"/pokemon/{blocked}")
    assert resp.status_code == 403


@pytest.mark.parametrize("correct", ["farfetchd", "mr-mime", "ho-oh", "nidoran-f"])
def test_api_spellings_of_tricky_names_work(api, correct):
    assert api.json(f"/pokemon/{correct}")["name"] == correct


def test_unknown_endpoint_is_a_client_error(api):
    # Observed: 400 rather than 404 for an unknown resource type.
    assert 400 <= api.get("/pokemonz/25").status_code < 500


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_write_methods_are_rejected(session, method):
    resp = session.request(method, f"{BASE_URL}/pokemon/25", timeout=TIMEOUT)
    assert resp.status_code == 403  # docs: only GET/HEAD/OPTIONS are allowed


@pytest.mark.parametrize("method, status", [("HEAD", 200), ("OPTIONS", 204)])
def test_read_only_methods_are_allowed(session, method, status):
    assert session.request(method, f"{BASE_URL}/pokemon/25", timeout=TIMEOUT).status_code == status


# --- Headers and performance ------------------------------------------------

def test_response_headers(session):
    resp = session.get(f"{BASE_URL}/pokemon/gengar", timeout=TIMEOUT)
    assert resp.headers["Content-Type"] == "application/json; charset=utf-8"
    assert resp.headers["Access-Control-Allow-Origin"] == "*"  # usable from browser apps
    assert "public" in resp.headers["Cache-Control"]
    assert "ETag" in resp.headers


def test_response_time_is_reasonable(session):
    start = time.perf_counter()
    resp = session.get(f"{BASE_URL}/pokemon/dragonite", timeout=TIMEOUT)
    elapsed = time.perf_counter() - start
    assert resp.status_code == 200
    assert elapsed < 2.0, f"took {elapsed:.2f}s"
