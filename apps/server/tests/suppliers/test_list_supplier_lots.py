"""GET /suppliers/{supplierId}/lots: 200 `LotList`, 401 and 404 (format `Error`).

Only the available lots: something left to reserve, pickup window not over and use-by
date not passed. Any logged-in user: the contract lists no 403 for this route.
"""

from datetime import UTC, datetime, timedelta

import httpx2
import pytest
from fastapi.testclient import TestClient

from tests.lots.helpers import LOT_FIELDS, assert_error, assert_supplier_summary, at, today
from tests.prism import API_PREFIX, assert_contract
from tests.suppliers.conftest import PART_DIEU, VILLEURBANNE


def _path(supplier_id) -> str:
    return f"/suppliers/{supplier_id}/lots"


def _ids(response) -> list[int]:
    return [lot["id"] for lot in response.json()["data"]]


# ----- 200 -----


def test_list_supplier_lots(api: httpx2.Client, association_headers: dict, supplier_at, add_lot):
    supplier = supplier_at(PART_DIEU)
    lot = add_lot(supplier)

    response = api.get(_path(supplier.id), headers=association_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"data"}
    [item] = data["data"]
    assert set(item) == LOT_FIELDS
    assert item["id"] == lot.id
    assert item["status"] == "available"
    assert_supplier_summary(item["supplier"], supplier)


def test_list_supplier_lots_available_only(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    supplier = supplier_at(PART_DIEU)
    available = add_lot(supplier)
    add_lot(supplier, remaining_quantity=0)  # reserved: nothing left
    yesterday = datetime.now(UTC) - timedelta(days=1)
    add_lot(supplier, pickup_start=yesterday - timedelta(hours=2), pickup_end=yesterday)
    add_lot(supplier, use_by_date=today() - timedelta(days=1))  # use-by date passed

    response = api.get(_path(supplier.id), headers=association_headers)

    assert_contract(response)
    assert _ids(response) == [available.id]


def test_list_supplier_lots_partly_reserved_is_available(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    supplier = supplier_at(PART_DIEU)
    lot = add_lot(supplier, quantity=30, remaining_quantity=5)

    response = api.get(_path(supplier.id), headers=association_headers)

    assert_contract(response)
    assert _ids(response) == [lot.id]


def test_list_supplier_lots_of_this_supplier_only(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    supplier, other = supplier_at(PART_DIEU), supplier_at(VILLEURBANNE)
    mine = add_lot(supplier)
    add_lot(other)

    response = api.get(_path(supplier.id), headers=association_headers)

    assert_contract(response)
    assert _ids(response) == [mine.id]


def test_list_supplier_lots_soonest_pickup_first(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    supplier = supplier_at(PART_DIEU)
    in_two_days = today() + timedelta(days=2)
    later = add_lot(supplier, pickup_start=at(in_two_days, 13), pickup_end=at(in_two_days, 15))
    sooner = add_lot(supplier)  # tomorrow

    response = api.get(_path(supplier.id), headers=association_headers)

    assert_contract(response)
    assert _ids(response) == [sooner.id, later.id]


def test_list_supplier_lots_empty(api: httpx2.Client, association_headers: dict, supplier_at):
    response = api.get(_path(supplier_at(PART_DIEU).id), headers=association_headers)

    assert_contract(response)
    assert response.status_code == 200
    assert response.json() == {"data": []}


@pytest.mark.parametrize("reader", ["supplier_headers", "admin_headers"])
def test_list_supplier_lots_by_any_logged_in_user(
    api: httpx2.Client, request, reader: str, supplier_at, add_lot
):
    """The contract has no 403 here: any logged-in user can list the lots."""
    supplier = supplier_at(PART_DIEU)
    add_lot(supplier)

    response = api.get(_path(supplier.id), headers=request.getfixturevalue(reader))

    assert_contract(response)
    assert response.status_code == 200


# ----- 401 -----


def test_list_supplier_lots_without_token(api: httpx2.Client, supplier_at):
    response = api.get(_path(supplier_at(PART_DIEU).id))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")


def test_list_supplier_lots_invalid_token(api: httpx2.Client, supplier_at):
    response = api.get(
        _path(supplier_at(PART_DIEU).id), headers={"Authorization": "Bearer not-a-jwt"}
    )

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


# ----- 404 -----


def test_list_supplier_lots_unknown_supplier(api: httpx2.Client, association_headers: dict):
    response = api.get(_path(999), headers=association_headers)

    assert_contract(response)
    assert_error(response, 404, "not_found")


@pytest.mark.parametrize("supplier_id", ["abc", "0", "-1", str(2**63)])
def test_list_supplier_lots_impossible_id(
    client: TestClient, association_headers: dict, supplier_id: str
):
    """The contract has no 400/422 here: an id that cannot exist is not found.

    Sent in-process: through Prism, an id that is not an int64 is a request violation.
    """
    response = client.get(API_PREFIX + _path(supplier_id), headers=association_headers)

    assert_error(response, 404, "not_found")
