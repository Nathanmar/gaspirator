"""GET /lots/{lotId}: 200 `Lot`, 401, 403 and 404 (format `Error`).

Accessible to the associations and to the supplier that published the lot.
"""

from datetime import UTC, datetime, timedelta

import httpx2
import pytest

from app.schemas import SupplierType
from tests.lots.helpers import LOT_FIELDS, assert_error, assert_supplier_summary, at, parse, today
from tests.prism import assert_contract


def _path(lot_id) -> str:
    return f"/lots/{lot_id}"


# ----- 200 -----


def test_get_lot_as_its_supplier(api: httpx2.Client, supplier_headers: dict, supplier, create_lot):
    lot = create_lot(allergens=["milk", "eggs"])

    response = api.get(_path(lot.id), headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == LOT_FIELDS
    assert data["id"] == lot.id
    assert_supplier_summary(data["supplier"], supplier)
    assert data["title"] == "Hachis parmentier"
    assert data["category"] == "prepared_meal"
    assert data["quantity"] == 30
    assert data["remaining_quantity"] == 30
    assert data["unit"] == "portions"
    assert data["divisible"] is True
    assert data["use_by_date"] == lot.use_by_date.isoformat()
    assert sorted(data["allergens"]) == ["eggs", "milk"]
    assert data["storage"] == "refrigerated"
    assert parse(data["pickup_start"]) == lot.pickup_start
    assert parse(data["pickup_end"]) == lot.pickup_end
    assert data["status"] == "available"


def test_get_lot_as_association(api: httpx2.Client, association_headers: dict, create_lot):
    lot = create_lot()

    response = api.get(_path(lot.id), headers=association_headers)

    assert_contract(response)
    assert response.status_code == 200
    assert response.json()["id"] == lot.id


def test_get_lot_after_creation(api: httpx2.Client, supplier_headers: dict, lot_body: dict):
    created = api.post("/lots", json=lot_body, headers=supplier_headers).json()

    response = api.get(_path(created["id"]), headers=supplier_headers)

    assert_contract(response)
    assert response.json() == created


def test_get_lot_pickup_window_over(api: httpx2.Client, association_headers: dict, create_lot):
    """A lot whose pickup window has ended with a quantity left is `expired`."""
    now = datetime.now(UTC)
    lot = create_lot(pickup_start=now - timedelta(hours=3), pickup_end=now - timedelta(hours=1))

    response = api.get(_path(lot.id), headers=association_headers)

    assert_contract(response)
    assert response.json()["status"] == "expired"


def test_get_lot_use_by_date_passed(api: httpx2.Client, association_headers: dict, create_lot):
    yesterday = today() - timedelta(days=1)
    lot = create_lot(
        use_by_date=yesterday,
        pickup_start=at(yesterday - timedelta(days=1), 13),
        pickup_end=at(yesterday - timedelta(days=1), 15),
    )

    response = api.get(_path(lot.id), headers=association_headers)

    assert_contract(response)
    assert response.json()["status"] == "expired"


def test_get_lot_fully_reserved(api: httpx2.Client, association_headers: dict, create_lot):
    lot = create_lot(quantity=12, remaining_quantity=0)

    response = api.get(_path(lot.id), headers=association_headers)

    assert_contract(response)
    data = response.json()
    assert data["status"] == "reserved"
    assert data["quantity"] == 12
    assert data["remaining_quantity"] == 0


def test_get_lot_partly_reserved(api: httpx2.Client, association_headers: dict, create_lot):
    lot = create_lot(quantity=30, remaining_quantity=18)

    response = api.get(_path(lot.id), headers=association_headers)

    assert_contract(response)
    assert response.json()["remaining_quantity"] == 18
    assert response.json()["status"] == "available"


# ----- 401 -----


def test_get_lot_without_token(api: httpx2.Client, create_lot):
    lot = create_lot()

    response = api.get(_path(lot.id))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_get_lot_invalid_token(api: httpx2.Client, create_lot):
    lot = create_lot()

    response = api.get(_path(lot.id), headers={"Authorization": "Bearer not-a-jwt"})

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


def test_get_unknown_lot_without_token(api: httpx2.Client):
    """Authentication is checked before the lot is looked up."""
    response = api.get(_path(999))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


def test_get_lot_of_another_supplier(
    api: httpx2.Client, create_supplier, create_user, auth_headers, create_lot
):
    lot = create_lot()
    other = create_supplier(name="Hôpital Édouard-Herriot", supplier_type=SupplierType.HOSPITAL)
    headers = auth_headers(create_user(email="hopital@example.org", supplier=other))

    response = api.get(_path(lot.id), headers=headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_get_lot_as_admin(api: httpx2.Client, admin_headers: dict, create_lot):
    lot = create_lot()

    response = api.get(_path(lot.id), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_get_lot_manager_without_organization(
    api: httpx2.Client, create_user, auth_headers, create_lot
):
    lot = create_lot()

    response = api.get(_path(lot.id), headers=auth_headers(create_user()))

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_get_unknown_lot_as_admin(api: httpx2.Client, admin_headers: dict):
    """Users who cannot read any lot get 403, so they cannot probe which lots exist."""
    response = api.get(_path(999), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


# ----- 404 -----


def test_get_unknown_lot(api: httpx2.Client, association_headers: dict):
    response = api.get(_path(999), headers=association_headers)

    assert_contract(response)
    assert_error(response, 404, "not_found")


def test_get_deleted_lot(api: httpx2.Client, supplier_headers: dict, create_lot, db):
    lot = create_lot()
    db.delete(lot)
    db.commit()

    response = api.get(_path(lot.id), headers=supplier_headers)

    assert_contract(response)
    assert_error(response, 404, "not_found")


@pytest.mark.parametrize("lot_id", ["abc", "1.5", "0", "-1", "9223372036854775808"])
def test_get_lot_invalid_id(api: httpx2.Client, association_headers: dict, lot_id: str):
    """The contract has no 400/422 here: an id that cannot exist is not found."""
    response = api.get(_path(lot_id), headers=association_headers)

    assert_contract(response, invalid_request=True)
    assert_error(response, 404, "not_found")
