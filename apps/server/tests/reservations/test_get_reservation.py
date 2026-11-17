"""GET /reservations/{reservationId}: 200 `Reservation`, 401, 403 and 404 (format `Error`).

For the association that reserved, with the pickup code, and for the supplier of the lot,
without it.
"""

from datetime import UTC, datetime

import httpx2
import pytest

from app.models import Reservation
from app.schemas import ReservationStatus, SupplierType
from tests.lots.helpers import assert_error, parse
from tests.prism import assert_contract
from tests.reservations.helpers import (
    RESERVATION_FIELDS,
    assert_association_summary,
    assert_lot_summary,
    reservation_path,
)


@pytest.fixture
def booked(create_lot, association, create_reservation) -> Reservation:
    """A `booked` reservation of a lot of `supplier` by `association`."""
    return create_reservation(create_lot(), association, quantity=12)


# ----- 200 -----


def test_get_reservation_as_its_association(
    api: httpx2.Client, association_headers: dict, booked: Reservation, association
):
    response = api.get(reservation_path(booked.id), headers=association_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == RESERVATION_FIELDS | {"pickup_code"}
    assert data["id"] == booked.id
    assert_lot_summary(data["lot"], booked.lot)
    assert_association_summary(data["association"], association)
    assert data["quantity"] == 12
    assert parse(data["pickup_at"]) == booked.pickup_at
    assert data["status"] == "booked"
    assert data["pickup_code"] == booked.pickup_code
    assert parse(data["created_at"]).tzinfo is not None
    assert data["collected_at"] is None


def test_get_reservation_as_supplier_of_the_lot(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation
):
    response = api.get(reservation_path(booked.id), headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == RESERVATION_FIELDS  # without the pickup code
    assert data["id"] == booked.id


def test_get_collected_reservation(
    api: httpx2.Client, association_headers: dict, association, create_lot, create_reservation
):
    collected_at = datetime.now(UTC).replace(microsecond=0)
    reservation = create_reservation(
        create_lot(), association, status=ReservationStatus.COLLECTED, collected_at=collected_at
    )

    response = api.get(reservation_path(reservation.id), headers=association_headers)

    assert_contract(response)
    assert response.json()["status"] == "collected"
    assert parse(response.json()["collected_at"]) == collected_at


def test_get_reservation_same_as_lot_list(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation
):
    """The supplier sees the same reservation here and in the reservations of the lot."""
    response = api.get(reservation_path(booked.id), headers=supplier_headers)
    listed = api.get(f"/lots/{booked.lot_id}/reservations", headers=supplier_headers)

    assert_contract(response)
    assert listed.json()["data"] == [response.json()]


# ----- 401 -----


def test_get_reservation_without_token(api: httpx2.Client, booked: Reservation):
    response = api.get(reservation_path(booked.id))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_get_reservation_invalid_token(api: httpx2.Client, booked: Reservation):
    response = api.get(reservation_path(booked.id), headers={"Authorization": "Bearer not-a-jwt"})

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


def test_get_unknown_reservation_without_token(api: httpx2.Client):
    """Authentication is checked before the reservation is looked up."""
    response = api.get(reservation_path(999))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


def test_get_reservation_of_another_association(
    api: httpx2.Client, create_association, create_user, auth_headers, booked: Reservation
):
    other = create_association(name="Secours populaire Lyon")
    headers = auth_headers(create_user(email="secours@example.org", association=other))

    response = api.get(reservation_path(booked.id), headers=headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_get_reservation_of_another_supplier(
    api: httpx2.Client, create_supplier, create_user, auth_headers, booked: Reservation
):
    other = create_supplier(name="Hôpital Édouard-Herriot", supplier_type=SupplierType.HOSPITAL)
    headers = auth_headers(create_user(email="hopital@example.org", supplier=other))

    response = api.get(reservation_path(booked.id), headers=headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_get_reservation_as_admin(api: httpx2.Client, admin_headers: dict, booked: Reservation):
    response = api.get(reservation_path(booked.id), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_get_reservation_manager_without_organization(
    api: httpx2.Client, create_user, auth_headers, booked: Reservation
):
    response = api.get(reservation_path(booked.id), headers=auth_headers(create_user()))

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_get_unknown_reservation_as_admin(api: httpx2.Client, admin_headers: dict):
    """Users who cannot read any reservation get 403, so they cannot probe which exist."""
    response = api.get(reservation_path(999), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


# ----- 404 -----


def test_get_unknown_reservation(api: httpx2.Client, association_headers: dict):
    response = api.get(reservation_path(999), headers=association_headers)

    assert_contract(response)
    assert_error(response, 404, "not_found")


@pytest.mark.parametrize("reservation_id", ["abc", "1.5", "0", "-1", "9223372036854775808"])
def test_get_reservation_invalid_id(
    api: httpx2.Client, association_headers: dict, reservation_id: str
):
    """The contract has no 400/422 here: an id that cannot exist is not found."""
    response = api.get(reservation_path(reservation_id), headers=association_headers)

    assert_contract(response, invalid_request=True)
    assert_error(response, 404, "not_found")
