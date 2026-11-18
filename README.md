# Chin - API Test

Automated tests for [PokéAPI](https://pokeapi.co/docs/v2), a free, read-only REST API of Pokémon game data
that needs no authentication. Written in **Python** with **pytest**, **requests**, and **jsonschema**.

![tests](https://github.com/dcpliskin/Chin---API-Test/actions/workflows/tests.yml/badge.svg)

## Running the tests

Requires Python 3 (developed and tested on 3.14; CI uses 3.14).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -v
```

Expected result: **141 passed, 2 xfailed** in about 5-15 seconds. The two `xfail`s are real API bugs
(see [Findings](#findings)). CI runs the same suite on every push and weekly on a schedule
(`.github/workflows/tests.yml`), so changes to the live API get noticed.

## Approach

PokéAPI is used mostly by players and fan sites, so the suite is organized around **what players actually look up**.
It uses a fixed set of Pokémon chosen to cover interesting cases: Squirtle, Blastoise, Skitty, Giratina, Dragonite,
Aegislash, Torterra, Psyduck, and Gengar.

| Module | Player question | Examples |
|---|---|---|
| `test_pokedex_lookup.py` | "Show me this Pokémon" | name/ID lookups agree; exact types, base stats and stat totals; hidden abilities; species info (generation, legendary, egg groups); schema validation; case-insensitive names |
| `test_type_matchups.py` | "What is it weak to?" | Dragonite and Torterra take 4x from Ice; Gengar is immune to Normal and Fighting; the type chart is checked for internal consistency |
| `test_evolution.py` | "How does it evolve?" | level (Squirtle 16/36), item (Skitty + Moon Stone), trade (Haunter → Gengar, plus Linking Cord in Legends: Arceus); Giratina has no evolutions |
| `test_forms.py` | "Megas and alternate forms" | Aegislash Blade swaps attack/defense; Giratina Origin; Mega stat totals are +100; G-Max keeps base stats |
| `test_moves.py` | "What does it learn, and when?" | Squirtle learns Hydro Pump at L42 in Red/Blue but L33 in Scarlet/Violet; move power/accuracy/PP; move history |
| `test_encounters.py` | "Where can I catch it?" | Giratina in Platinum's Distortion World; encounter levels and rates are valid |
| `test_api_behavior.py` | General API health | counts, pagination, 404s, blocked characters and methods, headers, response time |

**How expected values were chosen:**
- Every expected value was **observed from the live API first**, then compared with the docs, not taken from
  the docs or general knowledge alone. Several observations contradicted assumptions (see Findings).
- Only stable game data is pinned: Pokédex numbers, types, base stats, evolution methods. These live in one
  table, `tests/data/favorites.py`, so the tests stay readable.
- Data that grows over time is checked with **consistency rules**, not hard-coded numbers. For example, the `/pokemon`
  count (1351 today, and growing as new forms are added) must equal the number of entries found by walking every page.
- Relationships are checked in both directions: Pokémon ↔ species, move ↔ learner, and type A → B against B ← A.
- Responses are cached per test run (`tests/conftest.py`), following the API's fair-use policy. Tests that need a fresh
  request (methods, headers, timing) bypass the cache.
- I confirmed the suite can fail by breaking an expected value (Dragonite's stat total set to 601): the test failed as intended.

## Findings

Bugs and surprises found while testing:

| # | Finding | Severity | Test |
|---|---|---|---|
| 1 | **`limit=-1` drops one result**: returns 1350 of 1351 entries with no error. | Medium (silent data loss) | `test_negative_limit_does_not_drop_results` (xfail) |
| 2 | **A negative `offset` wraps to the end of the list** (`offset=-5` returns the last forms), and `next` points to `offset=-2`. Looks like Python negative slicing leaking through. | Low | `test_negative_offset_is_not_treated_as_from_the_end` (xfail) |
| 3 | **`/pokemon/giratina` and `/pokemon/aegislash` return 404.** Pokémon with several forms are stored under the form name (`giratina-altered`, `aegislash-shield`). The species endpoint accepts the bare name. This is a usability trap for players. | Low (by design, undocumented) | `test_multi_form_pokemon_need_form_name` |
| 4 | Docs say only `limit` and `offset` are allowed as query parameters, but `/pokemon?limit=5&foo=bar` returns **200** while `/pokemon/25?foo=bar` returns **403**, so the two are inconsistent. | Low (docs mismatch) | not automated, recorded here |
| 5 | Unknown endpoint (`/pokemonz/25`) returns **400**, not 404. Blocked characters (`farfetch'd`, `mr.mime`) and write methods return a **403 HTML page** from Cloudflare, not a JSON error. | Low | `test_api_behavior.py` |
| 6 | Name lookups are **case-insensitive** (`GENGAR` works), which the docs don't state. | Info | `test_name_lookup_is_case_insensitive` |
| 7 | `location_area_encounters` is a full URL, not a path as the docs suggest. | Info (docs mismatch) | `test_encounters_link_resolves` |

**One of my assumptions was wrong:** I first asserted that an encounter's `max_chance` is at most 100%.
The live data has values above 100 (e.g. 110 and 130 for Psyduck around the Sinnoh lakes). `max_chance` is the *sum* of every method's chance in an area
(e.g. walking 10% + 10% plus surfing 60% + 30% = 110). The test now checks that the total adds up exactly,
which is stricter than the original range check.

Known bugs are marked `xfail(strict=True)`, so the suite stays green, but CI alerts if a bug gets fixed (the test
then passes unexpectedly and fails the run). That's the signal to remove the marker.

## Assumptions

- Tests run against the live public API, so they depend on network access and PokéAPI being up. Stubbing was optional and not done (see next steps).
- Game data for released games doesn't change. If PokéAPI corrects a value, the matching entry in `favorites.py` needs updating.
- The 2-second response-time limit is a sanity check, not a performance benchmark.

## What I'd test next

- **Stubbed/contract tests:** record responses (e.g. `responses` or VCR.py) so the suite also runs offline and in
  CI without depending on the live service, and add contract tests for the schemas.
- **Wider data checks:** run the consistency checks (variety links, evolution ↔ species, type chart) across *all*
  1025 species in a nightly job, not just the sample.
- **More player questions:** held items and their rarity, Pokémon availability per game (version exclusives),
  egg-group breeding compatibility, abilities' effect text in other languages.
- **Non-functional:** cache behavior (`ETag` / `If-None-Match` → 304), behavior under rapid repeated requests,
  and very large pages (`limit=100000`).
- Report findings 1 and 2 upstream to the PokéAPI GitHub project.

## Project layout

```
tests/
  conftest.py          # session fixtures: HTTP session, cached API client
  helpers.py           # constants and pure helpers (stat totals, damage multipliers, chain search)
  schemas.py           # JSON Schemas for the response shapes the tests rely on
  data/favorites.py    # expected values, observed from the live API
  test_*.py            # one module per player question
.github/workflows/tests.yml   # CI: pytest on push, PR, and weekly
```
