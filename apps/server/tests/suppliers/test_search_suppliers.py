"""GET /suppliers: 200 `SupplierSearchPage`, 400, 401 and 403 (format `Error`).

Associations only. Suppliers with at least one available lot, nearest first; without
`latitude` and `longitude`, the position of the current association is used.
"""

from datetime import UTC, datetime, timedelta

import httpx2
import pytest

from tests.lots.helpers import assert_error, assert_supplier_summary, today
from tests.prism import assert_contract
from tests.suppliers.conftest import (
    GRENOBLE,
    LYON_CENTRE,
    NEUVILLE,
    PART_DIEU,
    VILLEURBANNE,
)
from tests.suppliers.helpers import SUPPLIER_SUMMARY_FIELDS, haversine_km

SUPPLIERS_PATH = "/suppliers"


def _ids(response) -> list[int]:
    return [supplier["id"] for supplier in response.json()["data"]]


# ----- 200 -----


def test_search_suppliers(api: httpx2.Client, association_headers: dict, supplier_at, add_lot):
    supplier = supplier_at(PART_DIEU)
    add_lot(supplier)

    response = api.get(SUPPLIERS_PATH, headers=association_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"data", "meta"}
    assert data["meta"] == {"page": 1, "per_page": 20, "total": 1}
    [result] = data["data"]
    assert set(result) == SUPPLIER_SUMMARY_FIELDS | {"distance_km", "available_lots_count"}
    assert_supplier_summary({key: result[key] for key in SUPPLIER_SUMMARY_FIELDS}, supplier)
    assert result["available_lots_count"] == 1


def test_search_suppliers_distance(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    """`distance_km` is the great-circle distance from the association (haversine)."""
    add_lot(supplier_at(VILLEURBANNE))

    response = api.get(SUPPLIERS_PATH, headers=association_headers)

    assert_contract(response)
    [result] = response.json()["data"]
    assert result["distance_km"] == pytest.approx(haversine_km(LYON_CENTRE, VILLEURBANNE), abs=0.01)


def test_search_suppliers_nearest_first(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    mid, near = supplier_at(VILLEURBANNE), supplier_at(PART_DIEU)
    add_lot(mid)
    add_lot(near)

    response = api.get(SUPPLIERS_PATH, headers=association_headers)

    assert_contract(response)
    assert _ids(response) == [near.id, mid.id]
    distances = [result["distance_km"] for result in response.json()["data"]]
    assert distances == sorted(distances)


def test_search_suppliers_default_radius_is_10_km(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    near, outside = supplier_at(PART_DIEU), supplier_at(NEUVILLE)
    add_lot(near)
    add_lot(outside)

    response = api.get(SUPPLIERS_PATH, headers=association_headers)

    assert_contract(response)
    assert _ids(response) == [near.id]
    assert response.json()["meta"]["total"] == 1


def test_search_suppliers_radius(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    near, outside = supplier_at(PART_DIEU), supplier_at(NEUVILLE)
    add_lot(near)
    add_lot(outside)

    response = api.get(SUPPLIERS_PATH, params={"radius_km": 20}, headers=association_headers)

    assert_contract(response)
    assert _ids(response) == [near.id, outside.id]


def test_search_suppliers_from_given_position(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    """`latitude` and `longitude` replace the position of the association."""
    add_lot(supplier_at(PART_DIEU))
    grenoble = supplier_at(GRENOBLE)
    add_lot(grenoble)
    latitude, longitude = GRENOBLE

    response = api.get(
        SUPPLIERS_PATH,
        params={"latitude": latitude, "longitude": longitude},
        headers=association_headers,
    )

    assert_contract(response)
    assert _ids(response) == [grenoble.id]
    assert response.json()["data"][0]["distance_km"] == pytest.approx(0, abs=0.001)


def test_search_suppliers_counts_available_lots_only(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    """Reserved (nothing left), finished pickup window and passed use-by date do not count."""
    supplier = supplier_at(PART_DIEU)
    add_lot(supplier)
    add_lot(supplier)
    add_lot(supplier, remaining_quantity=0)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    add_lot(supplier, pickup_start=yesterday - timedelta(hours=2), pickup_end=yesterday)
    add_lot(supplier, use_by_date=today() - timedelta(days=1))

    response = api.get(SUPPLIERS_PATH, headers=association_headers)

    assert_contract(response)
    assert response.json()["data"][0]["available_lots_count"] == 2


def test_search_suppliers_without_available_lot(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    """A supplier with no lot, or only lots that cannot be reserved, is not listed."""
    supplier_at(PART_DIEU)
    add_lot(supplier_at(VILLEURBANNE), remaining_quantity=0)

    response = api.get(SUPPLIERS_PATH, headers=association_headers)

    assert_contract(response)
    assert response.json() == {"data": [], "meta": {"page": 1, "per_page": 20, "total": 0}}


def test_search_suppliers_pagination(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    suppliers = [supplier_at(place) for place in (PART_DIEU, VILLEURBANNE, NEUVILLE)]
    for supplier in suppliers:
        add_lot(supplier)
    params = {"radius_km": 20, "per_page": 2}

    first = api.get(SUPPLIERS_PATH, params={**params, "page": 1}, headers=association_headers)
    second = api.get(SUPPLIERS_PATH, params={**params, "page": 2}, headers=association_headers)
    beyond = api.get(SUPPLIERS_PATH, params={**params, "page": 9}, headers=association_headers)

    for response in (first, second, beyond):
        assert_contract(response)
    assert _ids(first) == [suppliers[0].id, suppliers[1].id]
    assert _ids(second) == [suppliers[2].id]
    assert _ids(beyond) == []
    assert first.json()["meta"] == {"page": 1, "per_page": 2, "total": 3}
    assert beyond.json()["meta"] == {"page": 9, "per_page": 2, "total": 3}


# ----- 400 -----


@pytest.mark.parametrize(
    "params",
    [
        {"latitude": 91, "longitude": 4.8},
        {"latitude": 45.7, "longitude": -181},
        {"latitude": "abc", "longitude": 4.8},
        {"radius_km": 0},
        {"radius_km": 51},
        {"radius_km": 2.5},
        {"page": 0},
        {"per_page": 0},
        {"per_page": 101},
    ],
    ids=[
        "latitude-91",
        "longitude-minus-181",
        "latitude-text",
        "radius-0",
        "radius-51",
        "radius-not-integer",
        "page-0",
        "per-page-0",
        "per-page-101",
    ],
)
def test_search_suppliers_invalid_parameter(
    api: httpx2.Client, association_headers: dict, params: dict
):
    response = api.get(SUPPLIERS_PATH, params=params, headers=association_headers)

    assert_contract(response, invalid_request=True)
    data = assert_error(response, 400, "bad_request")
    assert {detail["field"] for detail in data["details"]} <= set(params)


@pytest.mark.parametrize("params", [{"latitude": 45.7}, {"longitude": 4.8}], ids=["lat", "lon"])
def test_search_suppliers_latitude_without_longitude(
    api: httpx2.Client, association_headers: dict, params: dict
):
    """Half a position is an incorrect parameter: both or neither."""
    response = api.get(SUPPLIERS_PATH, params=params, headers=association_headers)

    assert_contract(response)
    assert_error(response, 400, "bad_request")


# ----- 401 -----


def test_search_suppliers_without_token(api: httpx2.Client):
    response = api.get(SUPPLIERS_PATH)

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_search_suppliers_invalid_token(api: httpx2.Client):
    response = api.get(SUPPLIERS_PATH, headers={"Authorization": "Bearer not-a-jwt"})

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


def test_search_suppliers_as_supplier(api: httpx2.Client, supplier_headers: dict):
    response = api.get(SUPPLIERS_PATH, headers=supplier_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_search_suppliers_as_admin(api: httpx2.Client, admin_headers: dict):
    response = api.get(SUPPLIERS_PATH, headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_search_suppliers_as_supplier_with_invalid_parameter(
    api: httpx2.Client, supplier_headers: dict
):
    """The role is checked before the parameters."""
    response = api.get(SUPPLIERS_PATH, params={"radius_km": 0}, headers=supplier_headers)

    assert_contract(response, invalid_request=True)
    assert_error(response, 403, "forbidden")
