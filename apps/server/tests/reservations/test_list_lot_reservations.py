"""GET /lots/{lotId}/reservations: 200 `ReservationList`, 401, 403 and 404 (format `Error`).

Only for the supplier that published the lot; the pickup codes are not sent.
"""

from datetime import UTC, datetime, timedelta

import httpx2
import pytest

from app.schemas import ReservationStatus, SupplierType
from tests.lots.helpers import assert_error, iso, parse
from tests.prism import assert_contract
from tests.reservations.helpers import (
    RESERVATION_FIELDS,
    assert_association_summary,
    assert_lot_summary,
    reservations_path,
)

# ----- 200 -----


def test_list_lot_reservations(
    api: httpx2.Client, supplier_headers: dict, association, create_lot, create_reservation
):
    lot = create_lot(quantity=30)
    reservation = create_reservation(lot, association, quantity=12)

    response = api.get(reservations_path(lot.id), headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"data"}
    [item] = data["data"]
    assert set(item) == RESERVATION_FIELDS  # without the pickup code
    assert item["id"] == reservation.id
    assert_lot_summary(item["lot"], lot)
    assert_association_summary(item["association"], association)
    assert item["quantity"] == 12
    assert parse(item["pickup_at"]) == reservation.pickup_at
    assert item["status"] == "booked"
    assert parse(item["created_at"]).tzinfo is not None
    assert item["collected_at"] is None


def test_list_lot_without_reservations(api: httpx2.Client, supplier_headers: dict, create_lot):
    lot = create_lot()

    response = api.get(reservations_path(lot.id), headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 200
    assert response.json() == {"data": []}


def test_list_lot_reservations_most_recent_first(
    api: httpx2.Client,
    supplier_headers: dict,
    association,
    create_association,
    create_lot,
    create_reservation,
):
    lot = create_lot(quantity=30)
    first = create_reservation(lot, association, quantity=5)
    second = create_reservation(lot, create_association(name="Secours populaire"), quantity=7)
    third = create_reservation(lot, association, quantity=3)

    response = api.get(reservations_path(lot.id), headers=supplier_headers)

    assert_contract(response)
    assert [item["id"] for item in response.json()["data"]] == [third.id, second.id, first.id]


def test_list_lot_reservations_only_of_this_lot(
    api: httpx2.Client, supplier_headers: dict, association, create_lot, create_reservation
):
    lot = create_lot()
    other_lot = create_lot(title="Yaourts nature")
    reservation = create_reservation(lot, association)
    create_reservation(other_lot, association)

    response = api.get(reservations_path(lot.id), headers=supplier_headers)

    assert_contract(response)
    assert [item["id"] for item in response.json()["data"]] == [reservation.id]


def test_list_lot_reservations_collected(
    api: httpx2.Client, supplier_headers: dict, association, create_lot, create_reservation
):
    lot = create_lot()
    collected_at = datetime.now(UTC).replace(microsecond=0)
    create_reservation(
        lot, association, status=ReservationStatus.COLLECTED, collected_at=collected_at
    )

    response = api.get(reservations_path(lot.id), headers=supplier_headers)

    assert_contract(response)
    [item] = response.json()["data"]
    assert item["status"] == "collected"
    assert parse(item["collected_at"]) == collected_at


def test_list_lot_reservations_after_reservation(
    api: httpx2.Client, supplier_headers: dict, association_headers: dict, create_lot
):
    """What the association reserved, without its pickup code."""
    lot = create_lot()
    created = api.post(
        reservations_path(lot.id),
        json={"quantity": 12, "pickup_at": iso(lot.pickup_start + timedelta(minutes=30))},
        headers=association_headers,
    ).json()

    response = api.get(reservations_path(lot.id), headers=supplier_headers)

    assert_contract(response)
    del created["pickup_code"]
    assert response.json() == {"data": [created]}


# ----- 401 -----


def test_list_lot_reservations_without_token(api: httpx2.Client, create_lot):
    lot = create_lot()

    response = api.get(reservations_path(lot.id))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_list_lot_reservations_invalid_token(api: httpx2.Client, create_lot):
    lot = create_lot()

    response = api.get(reservations_path(lot.id), headers={"Authorization": "Bearer not-a-jwt"})

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


def test_list_unknown_lot_reservations_without_token(api: httpx2.Client):
    """Authentication is checked before the lot is looked up."""
    response = api.get(reservations_path(999))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


def test_list_lot_reservations_of_another_supplier(
    api: httpx2.Client, create_supplier, create_user, auth_headers, create_lot
):
    lot = create_lot()
    other = create_supplier(name="Hôpital Édouard-Herriot", supplier_type=SupplierType.HOSPITAL)
    headers = auth_headers(create_user(email="hopital@example.org", supplier=other))

    response = api.get(reservations_path(lot.id), headers=headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_list_lot_reservations_as_association(
    api: httpx2.Client, association_headers: dict, association, create_lot, create_reservation
):
    """Even the association that reserved the lot cannot list its reservations."""
    lot = create_lot()
    create_reservation(lot, association)

    response = api.get(reservations_path(lot.id), headers=association_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_list_lot_reservations_as_admin(api: httpx2.Client, admin_headers: dict, create_lot):
    lot = create_lot()

    response = api.get(reservations_path(lot.id), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_list_lot_reservations_manager_without_organization(
    api: httpx2.Client, create_user, auth_headers, create_lot
):
    lot = create_lot()

    response = api.get(reservations_path(lot.id), headers=auth_headers(create_user()))

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_list_unknown_lot_reservations_as_association(
    api: httpx2.Client, association_headers: dict
):
    """Users who cannot list any reservation get 403, so they cannot probe which lots exist."""
    response = api.get(reservations_path(999), headers=association_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


# ----- 404 -----


def test_list_unknown_lot_reservations(api: httpx2.Client, supplier_headers: dict):
    response = api.get(reservations_path(999), headers=supplier_headers)

    assert_contract(response)
    assert_error(response, 404, "not_found")


@pytest.mark.parametrize("lot_id", ["abc", "1.5", "0", "-1", "9223372036854775808"])
def test_list_lot_reservations_invalid_id(api: httpx2.Client, supplier_headers: dict, lot_id: str):
    """The contract has no 400/422 here: an id that cannot exist is not found."""
    response = api.get(reservations_path(lot_id), headers=supplier_headers)

    assert_contract(response, invalid_request=True)
    assert_error(response, 404, "not_found")
