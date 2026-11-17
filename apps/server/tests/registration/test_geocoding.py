"""`GeoplateformeGeocoder`: geocoding of the registration addresses with the Géoplateforme
(https://data.geopf.fr/geocodage), here replaced by a local HTTP server."""

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

from app.geocoding import MIN_SCORE, GeocodingUnavailable, GeoplateformeGeocoder
from app.schemas import Address, GeoPoint

ADDRESS = Address(street="12 rue de la République", postal_code="69002", city="Lyon")


def _feature(score: float = 0.97, lon: float = 4.835769, lat: float = 45.76511) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "label": "12 Rue de la République 69002 Lyon",
            "postcode": "69002",
            "city": "Lyon",
            "score": score,
            "type": "housenumber",
        },
    }


class StubGeoplateforme:
    """What the stub answers, and the requests it received."""

    def __init__(self) -> None:
        self.status = 200
        self.body: bytes = json.dumps({"type": "FeatureCollection", "features": []}).encode()
        self.requests: list[str] = []

    def answer(self, *features: dict) -> None:
        self.body = json.dumps({"type": "FeatureCollection", "features": list(features)}).encode()


@pytest.fixture
def stub() -> Iterator[tuple[StubGeoplateforme, str]]:
    """A local Géoplateforme; yields it and its base URL."""
    state = StubGeoplateforme()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            state.requests.append(self.path)
            self.send_response(state.status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(state.body)

        def log_message(self, *args) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state, f"http://127.0.0.1:{server.server_port}/geocodage"
    finally:
        server.shutdown()
        server.server_close()


def test_geocode_found(stub):
    state, url = stub
    state.answer(_feature())

    point = GeoplateformeGeocoder(url).geocode(ADDRESS)

    assert point == GeoPoint(latitude=45.76511, longitude=4.835769)


def test_geocode_query(stub):
    """Street and city in `q`, filtered on the postal code, best match only."""
    state, url = stub
    state.answer(_feature())

    GeoplateformeGeocoder(url).geocode(ADDRESS)

    [path] = state.requests
    request = urlsplit(path)
    assert request.path == "/geocodage/search"
    assert parse_qs(request.query) == {
        "q": ["12 rue de la République Lyon"],
        "index": ["address"],
        "postcode": ["69002"],
        "limit": ["1"],
    }


def test_geocode_no_result(stub):
    _, url = stub

    assert GeoplateformeGeocoder(url).geocode(ADDRESS) is None


def test_geocode_poor_match(stub):
    """A low score is another street nearby, not this address."""
    state, url = stub
    state.answer(_feature(score=MIN_SCORE - 0.01))

    assert GeoplateformeGeocoder(url).geocode(ADDRESS) is None


def test_geocode_match_at_min_score(stub):
    state, url = stub
    state.answer(_feature(score=MIN_SCORE))

    assert GeoplateformeGeocoder(url).geocode(ADDRESS) is not None


@pytest.mark.parametrize("status", [400, 500, 503])
def test_geocode_service_error(stub, status: int):
    state, url = stub
    state.status = status

    with pytest.raises(GeocodingUnavailable):
        GeoplateformeGeocoder(url).geocode(ADDRESS)


@pytest.mark.parametrize(
    "body", [b"<html>maintenance</html>", b'{"features": "none"}', b'{"features": [{}]}']
)
def test_geocode_unexpected_answer(stub, body: bytes):
    state, url = stub
    state.body = body

    with pytest.raises(GeocodingUnavailable):
        GeoplateformeGeocoder(url).geocode(ADDRESS)


def test_geocode_service_unreachable():
    with pytest.raises(GeocodingUnavailable):
        GeoplateformeGeocoder("http://127.0.0.1:9/geocodage", timeout=1).geocode(ADDRESS)
