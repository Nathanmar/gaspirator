"""POST /lots/{lotId}/reservations: 201 `Reservation`, 400, 401, 403, 404, 409 and 422
(format `Error`). Associations only.

A divisible lot is reserved for a chosen quantity, an indivisible lot as a whole. The
pickup time is within the pickup window of the lot, and the lot is never overbooked, even
by simultaneous requests.
"""

import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Lot, Reservation
from app.schemas import QuantityUnit, RegistrationStatus, SupplierType
from tests.lots.helpers import assert_error, at, iso, parse, today
from tests.prism import API_PREFIX, assert_contract
from tests.reservations.helpers import (
    RESERVATION_FIELDS,
    assert_association_summary,
    assert_lot_summary,
    reservations_path,
)


def _body(lot: Lot, **fields) -> dict:
    """A valid `ReservationCreate` body: 12 units, 30 minutes after the window opens."""
    return {"quantity": 12, "pickup_at": iso(lot.pickup_start + timedelta(minutes=30)), **fields}


def _reservation_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Reservation))


def _remaining(db: Session, lot: Lot) -> Decimal:
    db.refresh(lot)
    return lot.remaining_quantity


# ----- 201 -----


def test_create_reservation(
    api: httpx2.Client, association_headers: dict, association, create_lot, db: Session
):
    lot = create_lot(quantity=30)
    body = _body(lot)

    response = api.post(reservations_path(lot.id), json=body, headers=association_headers)

    assert_contract(response)
    assert response.status_code == 201
    data = response.json()
    assert set(data) == RESERVATION_FIELDS | {"pickup_code"}
    assert isinstance(data["id"], int)
    assert_lot_summary(data["lot"], lot)
    assert_association_summary(data["association"], association)
    assert data["quantity"] == 12
    assert parse(data["pickup_at"]) == parse(body["pickup_at"])
    assert data["status"] == "booked"
    assert re.fullmatch(r"\d{6}", data["pickup_code"])
    assert parse(data["created_at"]).tzinfo is not None
    assert data["collected_at"] is None

    reservation = db.get(Reservation, data["id"])
    assert reservation.lot_id == lot.id
    assert reservation.association_id == association.id
    assert reservation.quantity == 12
    assert reservation.pickup_code == data["pickup_code"]
    assert _remaining(db, lot) == 18


def test_reserve_whole_remaining_quantity(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    """Once nothing is left, the lot is `reserved`."""
    lot = create_lot(quantity=12)

    response = api.post(reservations_path(lot.id), json=_body(lot), headers=association_headers)

    assert_contract(response)
    assert response.status_code == 201
    assert _remaining(db, lot) == 0
    lot_response = api.get(f"/lots/{lot.id}", headers=association_headers)
    assert lot_response.json()["status"] == "reserved"


def test_reserve_indivisible_lot(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    """Without a quantity, the reservation is for the whole lot."""
    lot = create_lot(quantity=25, divisible=False)
    body = _body(lot)
    del body["quantity"]

    response = api.post(reservations_path(lot.id), json=body, headers=association_headers)

    assert_contract(response)
    assert response.status_code == 201
    assert response.json()["quantity"] == 25
    assert response.json()["lot"]["divisible"] is False
    assert _remaining(db, lot) == 0


def test_reserve_indivisible_lot_with_its_whole_quantity(
    api: httpx2.Client, association_headers: dict, create_lot
):
    lot = create_lot(quantity=25, divisible=False)

    response = api.post(
        reservations_path(lot.id), json=_body(lot, quantity=25), headers=association_headers
    )

    assert_contract(response)
    assert response.status_code == 201
    assert response.json()["quantity"] == 25


def test_reserve_fractional_quantity(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    """Quantities are exact decimals: the remaining quantity never drifts."""
    lot = create_lot(quantity=Decimal("2.5"), unit=QuantityUnit.KG)

    response = api.post(
        reservations_path(lot.id), json=_body(lot, quantity=0.1), headers=association_headers
    )

    assert_contract(response)
    assert response.status_code == 201
    assert response.json()["quantity"] == 0.1
    assert db.get(Reservation, response.json()["id"]).quantity == Decimal("0.1")
    assert _remaining(db, lot) == Decimal("2.4")


@pytest.mark.parametrize("bound", ["pickup_start", "pickup_end"])
def test_reserve_at_window_bounds(
    api: httpx2.Client, association_headers: dict, create_lot, bound: str
):
    lot = create_lot()

    response = api.post(
        reservations_path(lot.id),
        json=_body(lot, pickup_at=iso(getattr(lot, bound))),
        headers=association_headers,
    )

    assert_contract(response)
    assert response.status_code == 201


def test_reserve_during_pickup_window(api: httpx2.Client, association_headers: dict, create_lot):
    """A lot can still be reserved once its pickup window has opened."""
    now = datetime.now(UTC)
    lot = create_lot(pickup_start=now - timedelta(hours=1), pickup_end=now + timedelta(hours=1))

    response = api.post(
        reservations_path(lot.id),
        json=_body(lot, pickup_at=iso(now + timedelta(minutes=30))),
        headers=association_headers,
    )

    assert_contract(response)
    assert response.status_code == 201


def test_reserve_pickup_at_with_offset(api: httpx2.Client, association_headers: dict, create_lot):
    """Any offset is accepted; the pickup time is answered in UTC."""
    lot = create_lot()
    paris = lot.pickup_start.astimezone(timezone(timedelta(hours=1)))

    response = api.post(
        reservations_path(lot.id),
        json=_body(lot, pickup_at=paris.isoformat()),
        headers=association_headers,
    )

    assert_contract(response)
    assert response.status_code == 201
    pickup_at = parse(response.json()["pickup_at"])
    assert pickup_at == lot.pickup_start
    assert pickup_at.utcoffset() == timedelta(0)


def test_two_associations_share_a_lot(
    api: httpx2.Client,
    association_headers: dict,
    create_association,
    create_user,
    auth_headers,
    create_lot,
    db: Session,
):
    lot = create_lot(quantity=30)
    other = create_association(name="Secours populaire Lyon")
    other_headers = auth_headers(create_user(email="secours@example.org", association=other))

    first = api.post(reservations_path(lot.id), json=_body(lot), headers=association_headers)
    second = api.post(
        reservations_path(lot.id), json=_body(lot, quantity=18), headers=other_headers
    )

    assert first.status_code == second.status_code == 201
    assert second.json()["association"]["id"] == other.id
    assert first.json()["pickup_code"] != second.json()["pickup_code"]
    assert _remaining(db, lot) == 0


def test_simultaneous_reservations_never_overbook(
    api: httpx2.Client,
    prism_url: str,
    create_association,
    create_user,
    auth_headers,
    create_lot,
    db: Session,
):
    """10 portions, 8 associations asking for 3 at the same time: exactly 3 get them."""
    lot = create_lot(quantity=10)
    all_headers = [
        auth_headers(
            create_user(email=f"asso{index}@example.org", association=create_association())
        )
        for index in range(8)
    ]
    body = _body(lot, quantity=3)
    barrier = threading.Barrier(len(all_headers))

    def reserve(headers: dict) -> httpx2.Response:
        with httpx2.Client(base_url=prism_url, timeout=30) as http_client:
            barrier.wait()
            return http_client.post(reservations_path(lot.id), json=body, headers=headers)

    with ThreadPoolExecutor(max_workers=len(all_headers)) as pool:
        responses = list(pool.map(reserve, all_headers))

    for response in responses:
        assert_contract(response)
    assert sorted(response.status_code for response in responses) == [201] * 3 + [409] * 5
    assert _reservation_count(db) == 3
    assert _remaining(db, lot) == 1


# ----- 400 -----


@pytest.mark.parametrize(
    "body",
    ["{", '{"quantity": 12,}', "not json"],
    ids=["unclosed", "trailing-comma", "plain-text"],
)
def test_create_reservation_malformed_json(
    client: TestClient, association_headers: dict, create_lot, body: str, db: Session
):
    """Sent in-process: Prism never answers a malformed JSON body."""
    lot = create_lot()

    response = client.post(
        API_PREFIX + reservations_path(lot.id),
        content=body,
        headers={**association_headers, "Content-Type": "application/json"},
    )

    assert_error(response, 400, "bad_request")
    assert _reservation_count(db) == 0


@pytest.mark.parametrize("lot_id", ["abc", "1.5", "0", "-1", "9223372036854775808"])
def test_create_reservation_invalid_lot_id(
    api: httpx2.Client, association_headers: dict, create_lot, lot_id: str
):
    """A lot id that is not a positive int64 is an incorrect parameter."""
    lot = create_lot()

    response = api.post(reservations_path(lot_id), json=_body(lot), headers=association_headers)

    assert_contract(response, invalid_request=True)
    data = assert_error(response, 400, "bad_request")
    assert [detail["field"] for detail in data["details"]] == ["lotId"]


# ----- 401 -----


def test_create_reservation_without_token(api: httpx2.Client, create_lot, db: Session):
    lot = create_lot()

    response = api.post(reservations_path(lot.id), json=_body(lot))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert _reservation_count(db) == 0


def test_create_reservation_invalid_token(api: httpx2.Client, create_lot):
    lot = create_lot()

    response = api.post(
        reservations_path(lot.id), json=_body(lot), headers={"Authorization": "Bearer not-a-jwt"}
    )

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


def test_create_reservation_without_token_and_body(api: httpx2.Client):
    """Authentication is checked before the lot and the body."""
    response = api.post(reservations_path(999), json={})

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


def test_create_reservation_as_supplier(
    api: httpx2.Client, supplier_headers: dict, create_lot, db: Session
):
    """Even the supplier of the lot cannot reserve it."""
    lot = create_lot()

    response = api.post(reservations_path(lot.id), json=_body(lot), headers=supplier_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")
    assert _reservation_count(db) == 0


def test_create_reservation_as_another_supplier(
    api: httpx2.Client, create_supplier, create_user, auth_headers, create_lot
):
    lot = create_lot()
    other = create_supplier(name="Hôpital Édouard-Herriot", supplier_type=SupplierType.HOSPITAL)
    headers = auth_headers(create_user(email="hopital@example.org", supplier=other))

    response = api.post(reservations_path(lot.id), json=_body(lot), headers=headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_create_reservation_as_admin(api: httpx2.Client, admin_headers: dict, create_lot):
    lot = create_lot()

    response = api.post(reservations_path(lot.id), json=_body(lot), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_create_reservation_manager_without_association(
    api: httpx2.Client, create_user, auth_headers, create_lot
):
    """A manager whose registration request is not approved yet has no association."""
    lot = create_lot()
    user = create_user(registration_status=RegistrationStatus.PENDING)

    response = api.post(reservations_path(lot.id), json=_body(lot), headers=auth_headers(user))

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_create_reservation_as_supplier_with_invalid_body(
    api: httpx2.Client, supplier_headers: dict, create_lot
):
    """The role is checked before the body."""
    lot = create_lot()

    response = api.post(reservations_path(lot.id), json={}, headers=supplier_headers)

    assert_contract(response, invalid_request=True)
    assert_error(response, 403, "forbidden")


def test_create_reservation_unknown_lot_as_admin(api: httpx2.Client, admin_headers: dict):
    """Users who cannot reserve get 403, so they cannot probe which lots exist."""
    response = api.post(
        reservations_path(999),
        json={"pickup_at": "2026-11-03T14:15:00Z"},
        headers=admin_headers,
    )

    assert_contract(response)
    assert_error(response, 403, "forbidden")


# ----- 404 -----


def test_create_reservation_unknown_lot(api: httpx2.Client, association_headers: dict):
    response = api.post(
        reservations_path(999),
        json={"quantity": 12, "pickup_at": "2026-11-03T14:15:00Z"},
        headers=association_headers,
    )

    assert_contract(response)
    assert_error(response, 404, "not_found")


# ----- 409 -----


def _assert_conflict(response, db: Session, lot: Lot, remaining: Decimal) -> None:
    """409 and nothing reserved."""
    assert_contract(response)
    assert_error(response, 409, "conflict")
    assert _reservation_count(db) == 0
    assert _remaining(db, lot) == remaining


def test_reserve_fully_reserved_lot(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    lot = create_lot(quantity=12, remaining_quantity=0)

    response = api.post(reservations_path(lot.id), json=_body(lot), headers=association_headers)

    _assert_conflict(response, db, lot, Decimal(0))


def test_reserve_reserved_indivisible_lot(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    lot = create_lot(quantity=25, remaining_quantity=0, divisible=False)
    body = _body(lot)
    del body["quantity"]

    response = api.post(reservations_path(lot.id), json=body, headers=association_headers)

    _assert_conflict(response, db, lot, Decimal(0))


def test_reserve_more_than_remaining(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    """Another association took part of the lot in the meantime."""
    lot = create_lot(quantity=30, remaining_quantity=10)

    response = api.post(
        reservations_path(lot.id), json=_body(lot, quantity=12), headers=association_headers
    )

    _assert_conflict(response, db, lot, Decimal(10))


def test_reserve_more_than_lot_quantity(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    lot = create_lot(quantity=30)

    response = api.post(
        reservations_path(lot.id), json=_body(lot, quantity=31), headers=association_headers
    )

    _assert_conflict(response, db, lot, Decimal(30))


def test_reserve_lot_after_pickup_window(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    """An expired lot is not available any more, whatever the pickup time asked."""
    now = datetime.now(UTC)
    lot = create_lot(pickup_start=now - timedelta(hours=3), pickup_end=now - timedelta(hours=1))

    response = api.post(reservations_path(lot.id), json=_body(lot), headers=association_headers)

    _assert_conflict(response, db, lot, Decimal(30))


def test_reserve_lot_after_use_by_date(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    yesterday = today() - timedelta(days=1)
    lot = create_lot(
        use_by_date=yesterday,
        pickup_start=at(yesterday - timedelta(days=1), 13),
        pickup_end=at(yesterday - timedelta(days=1), 15),
    )

    response = api.post(reservations_path(lot.id), json=_body(lot), headers=association_headers)

    _assert_conflict(response, db, lot, Decimal(30))


# ----- 422 -----


def _assert_validation_error(
    response, field: str, db: Session, *, invalid_request: bool = True
) -> None:
    """`invalid_request=False` for bodies that respect the schema but break a business rule."""
    assert_contract(response, invalid_request=invalid_request)
    data = assert_error(response, 422, "validation_error")
    assert field in [detail["field"] for detail in data["details"]]
    for detail in data["details"]:
        assert set(detail) == {"field", "message"}
        assert detail["message"]
    assert _reservation_count(db) == 0


def test_create_reservation_missing_pickup_at(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    lot = create_lot()

    response = api.post(
        reservations_path(lot.id), json={"quantity": 12}, headers=association_headers
    )

    _assert_validation_error(response, "pickup_at", db)


def test_reserve_divisible_lot_without_quantity(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    lot = create_lot(divisible=True)
    body = _body(lot)
    del body["quantity"]

    response = api.post(reservations_path(lot.id), json=body, headers=association_headers)

    _assert_validation_error(response, "quantity", db, invalid_request=False)
    assert _remaining(db, lot) == 30


@pytest.mark.parametrize("quantity", [10, 26])
def test_reserve_indivisible_lot_with_another_quantity(
    api: httpx2.Client, association_headers: dict, create_lot, quantity: int, db: Session
):
    lot = create_lot(quantity=25, divisible=False)

    response = api.post(
        reservations_path(lot.id), json=_body(lot, quantity=quantity), headers=association_headers
    )

    _assert_validation_error(response, "quantity", db, invalid_request=False)
    assert _remaining(db, lot) == 25


@pytest.mark.parametrize("quantity", [0, -5])
def test_create_reservation_quantity_not_positive(
    api: httpx2.Client, association_headers: dict, create_lot, quantity: int, db: Session
):
    lot = create_lot()

    response = api.post(
        reservations_path(lot.id), json=_body(lot, quantity=quantity), headers=association_headers
    )

    _assert_validation_error(response, "quantity", db)


def test_create_reservation_quantity_too_precise(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    """Quantities are stored with 3 decimals: more would be silently rounded."""
    lot = create_lot(unit=QuantityUnit.KG)

    response = api.post(
        reservations_path(lot.id), json=_body(lot, quantity=1.2345), headers=association_headers
    )

    _assert_validation_error(response, "quantity", db, invalid_request=False)


@pytest.mark.parametrize(
    "minutes", [-1, 121], ids=["before-window", "after-window"]
)  # the window lasts 2 hours
def test_create_reservation_pickup_outside_window(
    api: httpx2.Client, association_headers: dict, create_lot, minutes: int, db: Session
):
    lot = create_lot()

    response = api.post(
        reservations_path(lot.id),
        json=_body(lot, pickup_at=iso(lot.pickup_start + timedelta(minutes=minutes))),
        headers=association_headers,
    )

    _assert_validation_error(response, "pickup_at", db, invalid_request=False)
    assert _remaining(db, lot) == 30


def test_create_reservation_pickup_in_the_past(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    """Within an open pickup window, the pickup time cannot be already over."""
    now = datetime.now(UTC)
    lot = create_lot(pickup_start=now - timedelta(hours=1), pickup_end=now + timedelta(hours=1))

    response = api.post(
        reservations_path(lot.id),
        json=_body(lot, pickup_at=iso(now - timedelta(minutes=30))),
        headers=association_headers,
    )

    _assert_validation_error(response, "pickup_at", db, invalid_request=False)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quantity", "twelve"),
        ("pickup_at", "tomorrow"),
        ("pickup_at", "2026-11-03"),
    ],
)
def test_create_reservation_invalid_field(
    api: httpx2.Client, association_headers: dict, create_lot, field: str, value, db: Session
):
    lot = create_lot()

    response = api.post(
        reservations_path(lot.id), json=_body(lot, **{field: value}), headers=association_headers
    )

    _assert_validation_error(response, field, db)


def test_create_reservation_pickup_at_without_timezone(
    api: httpx2.Client, association_headers: dict, create_lot, db: Session
):
    """A date-time without offset is ambiguous (ISO 8601 / RFC 3339 require one)."""
    lot = create_lot()
    local = lot.pickup_start.replace(tzinfo=None) + timedelta(minutes=30)

    response = api.post(
        reservations_path(lot.id),
        json=_body(lot, pickup_at=local.isoformat()),
        headers=association_headers,
    )

    _assert_validation_error(response, "pickup_at", db)


@pytest.mark.parametrize("field", ["status", "pickup_code", "association_id"])
def test_create_reservation_unknown_field(
    api: httpx2.Client, association_headers: dict, create_lot, field: str, db: Session
):
    """additionalProperties: false (a client cannot choose its status or its pickup code)."""
    lot = create_lot()

    response = api.post(
        reservations_path(lot.id), json=_body(lot, **{field: "123456"}), headers=association_headers
    )

    _assert_validation_error(response, field, db)


def test_create_reservation_reports_every_invalid_field(
    api: httpx2.Client, association_headers: dict, create_lot
):
    lot = create_lot(divisible=True)

    response = api.post(
        reservations_path(lot.id),
        json={"pickup_at": iso(lot.pickup_end + timedelta(hours=1))},
        headers=association_headers,
    )

    assert_contract(response)
    data = assert_error(response, 422, "validation_error")
    assert {"quantity", "pickup_at"} <= {detail["field"] for detail in data["details"]}
