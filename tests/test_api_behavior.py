"""General API behavior: counts, pagination, errors, HTTP methods, and headers."""
import statistics
import time

import jsonschema
import pytest

from tests import schemas
from tests.helpers import BASE_URL, TIMEOUT

MIN_SPECIES_COUNT = 1025  # National Dex through Gen 9 (Pecharunt). A floor, so a new generation doesn't break the suite.


# --- Counts ---------------------------------------------------------------

def species_count(api) -> int:
    return api.json("/pokemon-species", limit=1)["count"]


def test_species_count_covers_national_dex(api):
    assert species_count(api) >= MIN_SPECIES_COUNT


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

    # One default Pokémon per species, numbered 1..N with no gaps, whatever N is today.
    assert base == list(range(1, species_count(api) + 1))
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


def test_last_page_boundary(api):
    count = first_count(api)
    page = api.json("/pokemon", limit=10, offset=count - 3)
    assert len(page["results"]) == 3
    assert page["next"] is None
    assert page["previous"] is not None


def test_limit_larger_than_count_returns_everything(api):
    count = first_count(api)
    page = api.json("/pokemon", limit=100000)
    assert len(page["results"]) == count
    assert page["next"] is None


@pytest.mark.parametrize("params, expected_len, expected_first", [
    ({"limit": 0}, 20, "bulbasaur"),        # silently falls back to the default page size
    ({"limit": "abc"}, 20, "bulbasaur"),    # same: no error for a non-numeric limit
    ({"limit": "1.5"}, 1, "bulbasaur"),     # decimal is truncated to 1
    ({"limit": 3, "offset": "abc"}, 3, "bulbasaur"),  # non-numeric offset falls back to 0
])
def test_invalid_paging_values_fall_back_silently(api, params, expected_len, expected_first):
    """Observed: invalid limit/offset values are not rejected; the API falls back (README finding #4)."""
    page = api.json("/pokemon", **params)
    assert len(page["results"]) == expected_len
    assert page["results"][0]["name"] == expected_first


@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: negative limit/offset are applied as a raw Python slice, "
                          "results[offset:offset+limit] (README finding #1)")
@pytest.mark.parametrize("offset, limit", [
    (None, -1),   # observed: [0:-1]  -> last entry silently dropped
    (-5, 3),      # observed: [-5:-2] -> entries from the END of the list
    (-5, 5),      # observed: [-5:0]  -> silently empty
    (3, -2),      # observed: [3:1]   -> silently empty
    (-1351, 3),   # observed: right entries, but `next` link points to offset=-1348
])
def test_negative_paging_values_are_rejected_or_clamped(api, offset, limit):
    """Correct behavior (the docs don't define it) is either:
    - a 4xx rejection, or
    - negatives treated as 0: a page that starts at the clamped offset, with the requested size
      (or, for a negative limit, the default 20 or the whole list), and links with no negative values.
    An empty page or entries from the end of the list are never acceptable.
    """
    params = {k: v for k, v in (("offset", offset), ("limit", limit)) if v is not None}
    resp = api.get("/pokemon", **params)
    if 400 <= resp.status_code < 500:
        return  # rejecting the input is correct

    page = resp.json()
    full = [p["name"] for p in api.json("/pokemon", limit=100000)["results"]]
    start = max(offset or 0, 0)
    remaining = len(full) - start
    allowed_sizes = {min(limit, remaining)} if limit and limit > 0 else {min(20, remaining), remaining}
    got = [p["name"] for p in page["results"]]

    assert len(got) in allowed_sizes, f"page size {len(got)}, expected one of {sorted(allowed_sizes)}"
    assert got == full[start:start + len(got)], "page doesn't start at the clamped offset"
    for link in (page["next"], page["previous"]):
        assert link is None or ("offset=-" not in link and "limit=-" not in link), f"negative value in link {link}"


# --- Errors -----------------------------------------------------------------

@pytest.mark.parametrize("bad", ["0", "-1", "99999", "notapokemon", "pikachuu"])
def test_unknown_pokemon_returns_json_404(api, bad):
    resp = api.get(f"/pokemon/{bad}")
    assert resp.status_code == 404
    assert resp.headers["Content-Type"].startswith("application/json")
    jsonschema.validate(resp.json(), schemas.NOT_FOUND)


@pytest.mark.parametrize("blocked", ["farfetch'd", "mr.mime"])
def test_names_with_blocked_symbols_are_rejected(api, blocked):
    # The docs say URLs containing . , * % ; : ' ! @ + [ are blocked at the edge (Cloudflare).
    # Observed: the block is an HTML page, not the API's JSON error format.
    resp = api.get(f"/pokemon/{blocked}")
    assert resp.status_code == 403
    assert resp.headers["Content-Type"].startswith("text/html")


@pytest.mark.parametrize("query, status", [
    ("/pokemon?foo=bar", 403),
    ("/pokemon/25?foo=bar", 403),
    ("/pokemon?foo=bar&limit=5", 403),
    ("/pokemon?limit=5&foo=bar", 200),     # same parameters as above, in a different order
    ("/pokemon/25?limit=5&foo=bar", 200),
])
def test_unknown_query_params_blocked_only_when_query_does_not_start_with_limit_or_offset(api, query, status):
    """The docs say only `limit` and `offset` are allowed. Observed: the block depends on
    parameter ORDER. A query that starts with limit/offset gets through with extra parameters.
    This test records the current behavior (README finding #3)."""
    resp = api.get(query)
    assert resp.status_code == status
    expected_type = "application/json" if status == 200 else "text/html"
    assert resp.headers["Content-Type"].startswith(expected_type)


@pytest.mark.parametrize("correct", ["farfetchd", "mr-mime", "ho-oh", "nidoran-f"])
def test_api_spellings_of_tricky_names_work(api, correct):
    assert api.json(f"/pokemon/{correct}")["name"] == correct


def test_unknown_endpoint_returns_json_400(api):
    # Observed: 400 (not 404) for an unknown resource type, in the API's JSON error format.
    resp = api.get("/pokemonz/25")
    assert resp.status_code == 400
    assert resp.headers["Content-Type"].startswith("application/json")
    assert resp.json() == {"status": 400, "message": "Invalid endpoint or resource formatting"}


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_write_methods_are_rejected(session, method):
    # Docs: only GET/HEAD/OPTIONS are allowed. Observed: blocked at the edge with an HTML page.
    resp = session.request(method, f"{BASE_URL}/pokemon/25", timeout=TIMEOUT)
    assert resp.status_code == 403
    assert resp.headers["Content-Type"].startswith("text/html")


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
    # Median of 3 requests, so one slow request on a shared CI runner doesn't fail the run.
    timings = []
    for _ in range(3):
        start = time.perf_counter()
        resp = session.get(f"{BASE_URL}/pokemon/dragonite", timeout=TIMEOUT)
        timings.append(time.perf_counter() - start)
        assert resp.status_code == 200
    median = statistics.median(timings)
    assert median < 2.0, f"median {median:.2f}s, samples {[round(t, 2) for t in timings]}"
