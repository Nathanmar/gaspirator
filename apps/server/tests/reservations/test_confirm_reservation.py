"""POST /reservations/{reservationId}/confirm: 200 `Reservation`, 400, 401, 403, 404, 409,
422 and 429 (format `Error`). Only for the supplier of the lot.

The right pickup code makes the reservation `collected`, and the lot too once it is fully
reserved and all its reservations are collected. A wrong code is a 422; after 5 wrong
codes, confirming this reservation is blocked for 15 minutes (429).
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Reservation
from app.schemas import RegistrationStatus, ReservationStatus, SupplierType
from tests.lots.helpers import assert_error, iso, parse
from tests.prism import API_PREFIX, assert_contract
from tests.reservations.helpers import (
    RESERVATION_FIELDS,
    assert_association_summary,
    assert_lot_summary,
    reservation_path,
    reservations_path,
)

WRONG_CODE = "999999"
MAX_WRONG_CODES = 5
LOCK = timedelta(minutes=15)


def _path(reservation_id) -> str:
    return reservation_path(reservation_id) + "/confirm"


@pytest.fixture
def booked(create_lot, association, create_reservation) -> Reservation:
    """A `booked` reservation of a lot of `supplier` by `association`."""
    return create_reservation(create_lot(), association, quantity=12)


def _confirm(api: httpx2.Client, reservation: Reservation, headers: dict, code: str):
    return api.post(_path(reservation.id), json={"pickup_code": code}, headers=headers)


def _reload(db: Session, reservation: Reservation) -> Reservation:
    db.refresh(reservation)
    return reservation


def _assert_still_booked(db: Session, reservation: Reservation) -> None:
    reservation = _reload(db, reservation)
    assert reservation.status == ReservationStatus.BOOKED
    assert reservation.collected_at is None


# ----- 200 -----


def test_confirm_reservation(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation, association, db: Session
):
    before = datetime.now(UTC)

    response = _confirm(api, booked, supplier_headers, booked.pickup_code)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == RESERVATION_FIELDS  # the supplier does not get the pickup code
    assert data["id"] == booked.id
    assert_lot_summary(data["lot"], booked.lot)
    assert_association_summary(data["association"], association)
    assert data["quantity"] == 12
    assert data["status"] == "collected"
    collected_at = parse(data["collected_at"])
    assert before - timedelta(seconds=1) <= collected_at <= datetime.now(UTC)

    reservation = _reload(db, booked)
    assert reservation.status == ReservationStatus.COLLECTED
    assert reservation.collected_at == collected_at


def test_confirm_after_some_wrong_codes(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation, db: Session
):
    """Below 5 wrong codes, the right one still works, and the count starts again."""
    for _ in range(MAX_WRONG_CODES - 1):
        assert _confirm(api, booked, supplier_headers, WRONG_CODE).status_code == 422

    response = _confirm(api, booked, supplier_headers, booked.pickup_code)

    assert_contract(response)
    assert response.status_code == 200
    assert _reload(db, booked).failed_confirmations == 0


def test_confirm_once_the_block_is_over(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation, db: Session
):
    for _ in range(MAX_WRONG_CODES):
        _confirm(api, booked, supplier_headers, WRONG_CODE)
    booked.confirmation_locked_until = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()

    response = _confirm(api, booked, supplier_headers, booked.pickup_code)

    assert_contract(response)
    assert response.status_code == 200


def test_wrong_codes_count_again_once_the_block_is_over(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation, db: Session
):
    """After the block, 5 new wrong codes are allowed before the next one."""
    for _ in range(MAX_WRONG_CODES):
        _confirm(api, booked, supplier_headers, WRONG_CODE)
    booked.confirmation_locked_until = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()

    responses = [
        _confirm(api, booked, supplier_headers, WRONG_CODE) for _ in range(MAX_WRONG_CODES + 1)
    ]

    assert [response.status_code for response in responses] == [422] * MAX_WRONG_CODES + [429]


def test_confirm_reservation_made_through_the_api(
    api: httpx2.Client, supplier_headers: dict, association_headers: dict, create_lot
):
    """The code the association received confirms its reservation, and it sees it collected."""
    lot = create_lot()
    created = api.post(
        reservations_path(lot.id),
        json={"quantity": 12, "pickup_at": iso(lot.pickup_start + timedelta(minutes=30))},
        headers=association_headers,
    ).json()

    response = api.post(
        _path(created["id"]),
        json={"pickup_code": created["pickup_code"]},
        headers=supplier_headers,
    )

    assert_contract(response)
    assert response.status_code == 200
    seen = api.get(reservation_path(created["id"]), headers=association_headers).json()
    assert seen["status"] == "collected"
    assert seen["collected_at"] == response.json()["collected_at"]


# ----- 200: status of the lot (`LotStatus`) -----


def _lot_status(api: httpx2.Client, lot, headers: dict) -> str:
    response = api.get(f"/lots/{lot.id}", headers=headers)
    assert_contract(response)
    return response.json()["status"]


def test_lot_collected_once_every_reservation_is(
    api: httpx2.Client,
    supplier_headers: dict,
    create_lot,
    association,
    create_association,
    create_reservation,
):
    """A lot fully reserved is `collected` once all its reservations are."""
    lot = create_lot(quantity=30)
    first = create_reservation(lot, association, quantity=12)
    second = create_reservation(lot, create_association(name="Secours populaire"), quantity=18)

    assert _confirm(api, first, supplier_headers, first.pickup_code).status_code == 200
    assert _lot_status(api, lot, supplier_headers) == "reserved"

    assert _confirm(api, second, supplier_headers, second.pickup_code).status_code == 200
    assert _lot_status(api, lot, supplier_headers) == "collected"


def test_lot_collected_in_my_lots(
    api: httpx2.Client, supplier_headers: dict, create_lot, association, create_reservation
):
    lot = create_lot(quantity=12)
    reservation = create_reservation(lot, association, quantity=12)
    _confirm(api, reservation, supplier_headers, reservation.pickup_code)

    response = api.get("/me/lots", headers=supplier_headers)

    assert_contract(response)
    assert [item["status"] for item in response.json()["data"]] == ["collected"]


def test_lot_partly_reserved_and_collected_stays_available(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation
):
    """Something is left to reserve: the lot is still `available`."""
    _confirm(api, booked, supplier_headers, booked.pickup_code)

    assert _lot_status(api, booked.lot, supplier_headers) == "available"


def test_collected_lot_cannot_be_reserved(
    api: httpx2.Client,
    supplier_headers: dict,
    association_headers: dict,
    create_lot,
    association,
    create_reservation,
):
    lot = create_lot(quantity=12)
    reservation = create_reservation(lot, association, quantity=12)
    _confirm(api, reservation, supplier_headers, reservation.pickup_code)

    response = api.post(
        reservations_path(lot.id),
        json={"quantity": 1, "pickup_at": iso(lot.pickup_start + timedelta(minutes=30))},
        headers=association_headers,
    )

    assert_contract(response)
    data = assert_error(response, 409, "conflict")
    assert "entièrement réservé" in data["message"]


# ----- 400 -----


@pytest.mark.parametrize(
    "body",
    ["{", '{"pickup_code": "100000",}', "not json"],
    ids=["unclosed", "trailing-comma", "plain-text"],
)
def test_confirm_reservation_malformed_json(
    client: TestClient, supplier_headers: dict, booked: Reservation, body: str, db: Session
):
    """Sent in-process: Prism never answers a malformed JSON body."""
    response = client.post(
        API_PREFIX + _path(booked.id),
        content=body,
        headers={**supplier_headers, "Content-Type": "application/json"},
    )

    assert_error(response, 400, "bad_request")
    _assert_still_booked(db, booked)


@pytest.mark.parametrize("reservation_id", ["abc", "1.5", "0", "-1", "9223372036854775808"])
def test_confirm_reservation_invalid_id(
    api: httpx2.Client, supplier_headers: dict, reservation_id: str
):
    """A reservation id that is not a positive int64 is an incorrect parameter."""
    response = api.post(
        _path(reservation_id), json={"pickup_code": "100000"}, headers=supplier_headers
    )

    assert_contract(response, invalid_request=True)
    data = assert_error(response, 400, "bad_request")
    assert [detail["field"] for detail in data["details"]] == ["reservationId"]


# ----- 401 -----


def test_confirm_reservation_without_token(api: httpx2.Client, booked: Reservation, db: Session):
    response = api.post(_path(booked.id), json={"pickup_code": booked.pickup_code})

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")
    assert response.headers["WWW-Authenticate"] == "Bearer"
    _assert_still_booked(db, booked)


def test_confirm_reservation_invalid_token(api: httpx2.Client, booked: Reservation):
    response = _confirm(api, booked, {"Authorization": "Bearer not-a-jwt"}, booked.pickup_code)

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


def test_confirm_reservation_without_token_and_body(api: httpx2.Client):
    """Authentication is checked before the reservation and the body."""
    response = api.post(_path(999), json={})

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


def test_confirm_reservation_as_its_association(
    api: httpx2.Client, association_headers: dict, booked: Reservation, db: Session
):
    """The association cannot confirm its own pickup, even with its code."""
    response = _confirm(api, booked, association_headers, booked.pickup_code)

    assert_contract(response)
    assert_error(response, 403, "forbidden")
    _assert_still_booked(db, booked)


def test_confirm_reservation_of_another_supplier(
    api: httpx2.Client, create_supplier, create_user, auth_headers, booked: Reservation, db
):
    other = create_supplier(name="Hôpital Édouard-Herriot", supplier_type=SupplierType.HOSPITAL)
    headers = auth_headers(create_user(email="hopital@example.org", supplier=other))

    response = _confirm(api, booked, headers, booked.pickup_code)

    assert_contract(response)
    assert_error(response, 403, "forbidden")
    _assert_still_booked(db, booked)


def test_wrong_codes_of_another_supplier_are_not_counted(
    api: httpx2.Client, create_supplier, create_user, auth_headers, booked: Reservation, db
):
    other = create_supplier(name="Hôpital Édouard-Herriot", supplier_type=SupplierType.HOSPITAL)
    headers = auth_headers(create_user(email="hopital@example.org", supplier=other))

    response = _confirm(api, booked, headers, WRONG_CODE)

    assert_error(response, 403, "forbidden")
    assert _reload(db, booked).failed_confirmations == 0


def test_confirm_reservation_as_admin(api: httpx2.Client, admin_headers: dict, booked: Reservation):
    response = _confirm(api, booked, admin_headers, booked.pickup_code)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_confirm_reservation_manager_without_supplier(
    api: httpx2.Client, create_user, auth_headers, booked: Reservation
):
    """A manager whose registration request is not approved yet has no supplier."""
    user = create_user(registration_status=RegistrationStatus.PENDING)

    response = _confirm(api, booked, auth_headers(user), booked.pickup_code)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_confirm_reservation_as_association_with_invalid_body(
    api: httpx2.Client, association_headers: dict, booked: Reservation
):
    """The role is checked before the body."""
    response = api.post(_path(booked.id), json={}, headers=association_headers)

    assert_contract(response, invalid_request=True)
    assert_error(response, 403, "forbidden")


def test_confirm_unknown_reservation_as_admin(api: httpx2.Client, admin_headers: dict):
    """Users who cannot confirm get 403, so they cannot probe which reservations exist."""
    response = api.post(_path(999), json={"pickup_code": "100000"}, headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


# ----- 404 -----


def test_confirm_unknown_reservation(api: httpx2.Client, supplier_headers: dict):
    response = api.post(_path(999), json={"pickup_code": "100000"}, headers=supplier_headers)

    assert_contract(response)
    assert_error(response, 404, "not_found")


# ----- 409 -----


def test_confirm_collected_reservation(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation, db: Session
):
    assert _confirm(api, booked, supplier_headers, booked.pickup_code).status_code == 200
    collected_at = _reload(db, booked).collected_at

    response = _confirm(api, booked, supplier_headers, booked.pickup_code)

    assert_contract(response)
    assert_error(response, 409, "conflict")
    assert _reload(db, booked).collected_at == collected_at


def test_wrong_code_on_collected_reservation(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation, db: Session
):
    """Nothing left to confirm: a wrong code is not counted either."""
    assert _confirm(api, booked, supplier_headers, booked.pickup_code).status_code == 200

    response = _confirm(api, booked, supplier_headers, WRONG_CODE)

    assert_contract(response)
    assert_error(response, 409, "conflict")
    assert _reload(db, booked).failed_confirmations == 0


# ----- 422 -----


def test_confirm_wrong_code(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation, db: Session
):
    response = _confirm(api, booked, supplier_headers, WRONG_CODE)

    assert_contract(response)
    data = assert_error(response, 422, "validation_error")
    assert [detail["field"] for detail in data["details"]] == ["pickup_code"]
    _assert_still_booked(db, booked)
    assert _reload(db, booked).failed_confirmations == 1


def test_confirm_code_of_another_reservation(
    api: httpx2.Client,
    supplier_headers: dict,
    booked: Reservation,
    create_association,
    create_reservation,
    db: Session,
):
    other = create_reservation(booked.lot, create_association(name="Secours populaire"))

    response = _confirm(api, booked, supplier_headers, other.pickup_code)

    assert_contract(response)
    assert_error(response, 422, "validation_error")
    _assert_still_booked(db, booked)


@pytest.mark.parametrize(
    "body",
    [{}, {"pickup_code": "12345"}, {"pickup_code": "1234567"}, {"pickup_code": "abcdef"},
     {"pickup_code": 100000}, {"pickup_code": "100000", "status": "collected"}],
    ids=["missing", "too-short", "too-long", "letters", "number", "unknown-field"],
)  # fmt: skip
def test_confirm_reservation_invalid_body(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation, body: dict, db: Session
):
    """A malformed body is not an attempt: it is not counted as a wrong code."""
    response = api.post(_path(booked.id), json=body, headers=supplier_headers)

    assert_contract(response, invalid_request=True)
    data = assert_error(response, 422, "validation_error")
    assert data["details"]
    _assert_still_booked(db, booked)
    assert _reload(db, booked).failed_confirmations == 0


# ----- 429 -----


def _assert_blocked(response) -> None:
    assert_contract(response)
    assert_error(response, 429, "too_many_requests")
    assert 0 < int(response.headers["Retry-After"]) <= LOCK.total_seconds()


def test_confirm_after_five_wrong_codes(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation, db: Session
):
    before = datetime.now(UTC)
    for _ in range(MAX_WRONG_CODES):
        assert _confirm(api, booked, supplier_headers, WRONG_CODE).status_code == 422

    response = _confirm(api, booked, supplier_headers, WRONG_CODE)

    _assert_blocked(response)
    locked_until = _reload(db, booked).confirmation_locked_until
    assert before + LOCK <= locked_until <= datetime.now(UTC) + LOCK


def test_right_code_while_blocked(
    api: httpx2.Client, supplier_headers: dict, booked: Reservation, db: Session
):
    for _ in range(MAX_WRONG_CODES):
        _confirm(api, booked, supplier_headers, WRONG_CODE)

    response = _confirm(api, booked, supplier_headers, booked.pickup_code)

    _assert_blocked(response)
    _assert_still_booked(db, booked)


def test_block_is_per_reservation(
    api: httpx2.Client,
    supplier_headers: dict,
    booked: Reservation,
    create_association,
    create_reservation,
):
    other = create_reservation(booked.lot, create_association(name="Secours populaire"))
    for _ in range(MAX_WRONG_CODES):
        _confirm(api, booked, supplier_headers, WRONG_CODE)

    response = _confirm(api, other, supplier_headers, other.pickup_code)

    assert_contract(response)
    assert response.status_code == 200


def test_simultaneous_wrong_codes_are_all_counted(
    api: httpx2.Client, prism_url: str, supplier_headers: dict, booked: Reservation, db: Session
):
    """10 wrong codes at the same time: 5 are checked, the others are blocked."""
    attempts = 10
    barrier = threading.Barrier(attempts)

    def confirm(_) -> httpx2.Response:
        with httpx2.Client(base_url=prism_url, timeout=30) as http_client:
            barrier.wait()
            return _confirm(http_client, booked, supplier_headers, WRONG_CODE)

    with ThreadPoolExecutor(max_workers=attempts) as pool:
        responses = list(pool.map(confirm, range(attempts)))

    for response in responses:
        assert_contract(response)
    statuses = sorted(response.status_code for response in responses)
    assert statuses == [422] * MAX_WRONG_CODES + [429] * (attempts - MAX_WRONG_CODES)
    assert _reload(db, booked).confirmation_locked_until is not None
