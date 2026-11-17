"""GET /suppliers/{supplierId}: 200 `SupplierProfile`, 401 and 404 (format `Error`).

Any logged-in user: the contract lists no 403 for this route.
"""

from datetime import timedelta

import httpx2
import pytest
from fastapi.testclient import TestClient

from tests.lots.helpers import assert_error, assert_supplier_summary, today
from tests.prism import API_PREFIX, assert_contract
from tests.suppliers.conftest import PART_DIEU
from tests.suppliers.helpers import SUPPLIER_SUMMARY_FIELDS


def _path(supplier_id) -> str:
    return f"/suppliers/{supplier_id}"


# ----- 200 -----


def test_get_supplier(api: httpx2.Client, association_headers: dict, supplier_at, add_lot):
    supplier = supplier_at(PART_DIEU)
    add_lot(supplier)
    add_lot(supplier)

    response = api.get(_path(supplier.id), headers=association_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == SUPPLIER_SUMMARY_FIELDS | {"available_lots_count"}
    assert_supplier_summary({key: data[key] for key in SUPPLIER_SUMMARY_FIELDS}, supplier)
    assert data["available_lots_count"] == 2
    assert "legal_id" not in data


def test_get_supplier_without_available_lot(
    api: httpx2.Client, association_headers: dict, supplier_at, add_lot
):
    """Unlike the search, the page of a supplier with nothing to give is found (count 0)."""
    supplier = supplier_at(PART_DIEU)
    add_lot(supplier, remaining_quantity=0)
    add_lot(supplier, use_by_date=today() - timedelta(days=1))

    response = api.get(_path(supplier.id), headers=association_headers)

    assert_contract(response)
    assert response.status_code == 200
    assert response.json()["available_lots_count"] == 0


@pytest.mark.parametrize("reader", ["supplier_headers", "admin_headers"])
def test_get_supplier_by_any_logged_in_user(api: httpx2.Client, request, reader: str, supplier_at):
    """The contract has no 403 here: any logged-in user can read the page."""
    supplier = supplier_at(PART_DIEU)

    response = api.get(_path(supplier.id), headers=request.getfixturevalue(reader))

    assert_contract(response)
    assert response.status_code == 200


# ----- 401 -----


def test_get_supplier_without_token(api: httpx2.Client, supplier_at):
    response = api.get(_path(supplier_at(PART_DIEU).id))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")


def test_get_supplier_invalid_token(api: httpx2.Client, supplier_at):
    response = api.get(
        _path(supplier_at(PART_DIEU).id), headers={"Authorization": "Bearer not-a-jwt"}
    )

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


# ----- 404 -----


def test_get_supplier_unknown(api: httpx2.Client, association_headers: dict):
    response = api.get(_path(999), headers=association_headers)

    assert_contract(response)
    assert_error(response, 404, "not_found")


@pytest.mark.parametrize("supplier_id", ["abc", "0", "-1", str(2**63)])
def test_get_supplier_impossible_id(
    client: TestClient, association_headers: dict, supplier_id: str
):
    """The contract has no 400/422 here: an id that cannot exist is not found.

    Sent in-process: through Prism, an id that is not an int64 is a request violation.
    """
    response = client.get(API_PREFIX + _path(supplier_id), headers=association_headers)

    assert_error(response, 404, "not_found")
