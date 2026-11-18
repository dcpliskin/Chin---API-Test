"""Shared fixtures for the PokéAPI test suite.

PokéAPI's fair-use policy asks clients to cache responses, so GET responses are
cached for the whole test session. Tests that need a fresh request (HTTP methods,
timing, headers) use the raw `session` fixture instead.
"""
import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from tests.helpers import BASE_URL, TIMEOUT

# Retry only transient failures (dropped connections, rate limiting, server errors), so a network
# blip in CI doesn't fail the run. 4xx responses such as 403/404 are never retried: they're results under test.
RETRY = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET", "HEAD", "OPTIONS"),
    raise_on_status=False,  # after the last retry, return the response so the test reports the real status
)


class PokeApi:
    def __init__(self, session: requests.Session):
        self.session = session
        self._cache: dict[str, requests.Response] = {}

    def url(self, path: str) -> str:
        """Accept either a path ('/pokemon/25') or a full URL taken from a response link."""
        if path.startswith("http"):
            return path
        return f"{BASE_URL}/{path.lstrip('/')}"

    def get(self, path: str, **params) -> requests.Response:
        """Cached GET. Returns the Response whatever its status code."""
        req = requests.Request("GET", self.url(path), params=params).prepare()
        if req.url not in self._cache:
            self._cache[req.url] = self.session.get(req.url, timeout=TIMEOUT)
        return self._cache[req.url]

    def json(self, path: str, **params):
        """GET that must succeed with JSON; returns the parsed body."""
        resp = self.get(path, **params)
        assert resp.status_code == 200, f"GET {resp.url} -> {resp.status_code}: {resp.text[:200]}"
        assert resp.headers["Content-Type"].startswith("application/json")
        return resp.json()


@pytest.fixture(scope="session")
def session():
    with requests.Session() as s:
        s.headers["User-Agent"] = "Chin-API-Test (pytest; github.com/dcpliskin/Chin---API-Test)"
        s.mount("https://", HTTPAdapter(max_retries=RETRY))
        yield s


@pytest.fixture(scope="session")
def api(session) -> PokeApi:
    return PokeApi(session)
