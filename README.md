# Chin - API Test

Automated tests for [PokéAPI](https://pokeapi.co/docs/v2), a free, read-only REST API of Pokémon game data
(no API key needed). Written in Python with pytest.

![tests](https://github.com/dcpliskin/Chin---API-Test/actions/workflows/tests.yml/badge.svg)

**At a glance**
- **227 tests** across 9 modules, organized around what Pokémon players actually look up
  (stats, type weaknesses, evolutions, moves, where to catch).
- **Every documented endpoint** is covered at least by a smoke test (see [Terms](#terms)).
- **2 real API bugs found** and documented as expected failures, plus several gaps between the docs and the real API
  ([Findings](#findings)).
- Runs in about 10 seconds against the live API. GitHub Actions runs it on every push and weekly.

## Quick start

Needs Python 3.10+ and internet access.

```bash
python -m venv .venv
```

Activate the virtual environment:

- Windows: `.venv\Scripts\activate`
- macOS / Linux: `source .venv/bin/activate`

Then:

```bash
python -m pip install -r requirements.txt
python -m pytest
```

Expected output ends with: **`225 passed, 2 xfailed`**. The 2 xfailed tests are the known API bugs below.
They are reported, not hidden, and do not fail the run.

## What's tested

The suite uses a fixed set of Pokémon picked to cover interesting cases: Squirtle, Blastoise, Skitty,
Giratina, Dragonite, Aegislash, Torterra, Psyduck, and Gengar.

| File (`tests/`) | Question it answers | Examples |
|---|---|---|
| `test_pokedex_lookup.py` | "Show me this Pokémon" | lookups by name and Pokédex number agree; exact types, base stats, hidden abilities, legendary status |
| `test_type_matchups.py` | "What is it weak to?" | Dragonite and Torterra take 4x damage from Ice; Gengar is immune to Normal and Fighting |
| `test_evolution.py` | "How does it evolve?" | Squirtle at levels 16 and 36; Skitty with a Moon Stone; Haunter by trading |
| `test_forms.py` | "What about Megas and other forms?" | Aegislash's Blade form swaps attack and defense; Mega forms gain +100 total stats |
| `test_moves.py` | "What does it learn, and when?" | Squirtle learns Hydro Pump at level 42 in Red/Blue but level 33 in Scarlet/Violet |
| `test_encounters.py` | "Where can I catch it?" | Giratina is in Platinum's Distortion World |
| `test_game_world.py` | "Which TM? Which regional Pokédex?" | TM30 teaches Shadow Ball in Platinum but a different move in Red/Blue |
| `test_api_behavior.py` | "Does the API behave correctly?" | counts, paging through results, error responses, blocked requests, headers, speed |
| `test_smoke_all_endpoints.py` | "Does every endpoint work?" | all 50 endpoints return a valid list, and its first item loads |

Coverage by docs section: **deep** for Pokémon, Evolution, Moves, Machines, Encounters, and Locations;
**moderate** for Games and Items; **smoke test only** for Berries, Contests, and Currencies (rarely looked up by players).

## Findings

| # | Finding | Severity |
|---|---|---|
| 1 | **Bug:** `?limit=-1` returns 1350 of 1351 Pokémon. One is silently dropped. | Medium |
| 2 | **Bug:** a negative `?offset` wraps around to the end of the list instead of being rejected. | Low |
| 3 | `/pokemon/giratina` and `/pokemon/aegislash` return 404. Pokémon with several forms must be requested by form name (`giratina-altered`). A trap for players; not documented. | Low |
| 4 | The docs say only `limit` and `offset` query parameters are allowed, but the block **depends on parameter order**: `?foo=bar&limit=5` is blocked (403) while `?limit=5&foo=bar` gets through (200), on lists and single records alike. | Low |
| 5 | Invalid paging values are **silently accepted** instead of rejected: `limit=0` and `limit=abc` return the default 20 results, `limit=1.5` returns 1, `offset=abc` starts at 0. | Low |
| 6 | Error formats are inconsistent: unknown names give a JSON 404, an unknown endpoint gives a JSON 400, and blocked characters or write requests give a 403 HTML page. | Low |
| 7 | Not in the docs: name lookups ignore capitalization (`GENGAR` works), and `location_area_encounters` is a full URL, not a path. | Info |

Bugs 1 and 2 have tests that assert the *correct* behavior and are marked as expected failures (`xfail`).
If PokéAPI fixes a bug, its test starts passing and the run flags it, so the marker can be removed.

**A wrong assumption, corrected:** I first assumed an encounter's `max_chance` could not exceed 100%.
The real data goes higher, because `max_chance` is the *total* of every way to find a Pokémon in an area
(e.g. walking 10% + 10% and surfing 60% + 30% = 110). The test now checks that the total adds up exactly.

## How the tests are designed

- **Expected values come from the live API,** checked against the docs. They are not written from memory.
  They live in one file, [`tests/data/favorites.py`](tests/data/favorites.py).
- **Numbers that grow are never hard-coded.** The total number of Pokémon is checked by paging through every
  result and comparing with the reported count. A new game adding Pokémon doesn't break the suite.
- **Links are checked in both directions,** e.g. Gengar's move list includes Shadow Ball, *and* Shadow Ball's list of
  learners includes Gengar.
- **Responses are cached during a run,** as PokéAPI's fair-use policy asks.
- **Network blips don't fail the run:** dropped connections, rate limiting (429), and server errors (5xx) are retried
  up to 3 times. Error responses under test (403, 404, 400) are never retried. The speed check uses the median of 3 requests.
- **The tests can actually fail:** while writing the suite, I manually changed expected values (e.g. Dragonite's stat
  total) and confirmed the matching tests failed.

**When a new Pokémon game comes out:** new Pokémon, forms, and games don't break anything. A test fails only if a
new game *rebalances* one of the test Pokémon (e.g. changes its stats), because expected values reflect the latest
game. In that case, check the Pokémon's `past_stats` / `past_abilities` / `past_types` fields in the API. If the old
value moved there, the change is intentional: update `favorites.py`. A test also fails on purpose if PokéAPI adds or
removes an endpoint, so the smoke-test list stays current.

## Limitations and next steps

- Runs against the live API, so it needs the network and PokéAPI being up. **Next:** record responses
  (e.g. VCR.py) so the suite also runs offline.
- The response-time check (median under 2 seconds) is a sanity check, not a performance test.
- **Next:** run the consistency checks across all 1025 species nightly, not just the sample; pin expected
  values to a fixed generation using the `past_*` fields so rebalances never break tests; check caching
  (`ETag` → 304); report bugs 1 and 2 to the PokéAPI project.

## Terms

- **xfail:** a pytest marker for a test that is *expected* to fail, used here for confirmed bugs.
- **Smoke test:** a quick check that something basically works (here: each endpoint responds with valid data).
- **Base stat total:** the sum of a Pokémon's six base stats, a common way players compare Pokémon.

## Project layout

```
tests/
  conftest.py          shared setup: HTTP session and a cached API client
  helpers.py           small functions (stat totals, damage multipliers, evolution-chain search)
  schemas.py           JSON Schemas for the response shapes the tests rely on
  data/favorites.py    expected values for the test Pokémon
  test_*.py            the tests, one file per question above
.github/workflows/tests.yml   GitHub Actions: runs the suite on push and weekly
```
