"""`GeoplateformeGeocoder`: geocoding of the registration addresses with the Géoplateforme
(https://data.geopf.fr/geocodage), here replaced by a local HTTP server."""

import pytest

from app.geocoding import MIN_SCORE, GeocodingUnavailable, GeoplateformeGeocoder
from app.schemas import Address, GeoPoint
from tests.http_stub import stub_api

ADDRESS = Address(street="12 rue de la République", postal_code="69002", city="Lyon")


def _features(*features: dict) -> dict:
    return {"type": "FeatureCollection", "features": list(features)}


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


@pytest.fixture
def stub():
    """A local Géoplateforme (no result by default); yields it and its base URL."""
    with stub_api() as (state, url):
        state.answer_json(_features())
        yield state, url + "/geocodage"


def test_geocode_found(stub):
    state, url = stub
    state.answer_json(_features(_feature()))

    point = GeoplateformeGeocoder(url).geocode(ADDRESS)

    assert point == GeoPoint(latitude=45.76511, longitude=4.835769)


def test_geocode_query(stub):
    """Street and city in `q`, filtered on the postal code, best match only."""
    state, url = stub
    state.answer_json(_features(_feature()))

    GeoplateformeGeocoder(url).geocode(ADDRESS)

    path, query, _ = state.last_request
    assert path == "/geocodage/search"
    assert query == {
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
    state.answer_json(_features(_feature(score=MIN_SCORE - 0.01)))

    assert GeoplateformeGeocoder(url).geocode(ADDRESS) is None


def test_geocode_match_at_min_score(stub):
    state, url = stub
    state.answer_json(_features(_feature(score=MIN_SCORE)))

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
