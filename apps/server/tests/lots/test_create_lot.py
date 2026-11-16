"""POST /lots: 201 `Lot`, 400, 401, 403 and 422 (format `Error`). Suppliers only."""

from datetime import timedelta
from decimal import Decimal

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Lot
from app.schemas import RegistrationStatus, SupplierType
from tests.lots.helpers import (
    LOT_FIELDS,
    assert_error,
    assert_supplier_summary,
    at,
    iso,
    parse,
    today,
)
from tests.prism import API_PREFIX, assert_contract

LOTS_PATH = "/lots"


def _lot_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Lot))


# ----- 201 -----


def test_create_lot(api: httpx2.Client, supplier_headers: dict, supplier, lot_body: dict, db):
    response = api.post(LOTS_PATH, json=lot_body, headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 201
    data = response.json()
    assert set(data) == LOT_FIELDS
    assert isinstance(data["id"], int)
    assert_supplier_summary(data["supplier"], supplier)
    for field in ("title", "category", "unit", "divisible", "use_by_date", "storage"):
        assert data[field] == lot_body[field]
    assert data["quantity"] == 30
    assert data["remaining_quantity"] == 30
    assert sorted(data["allergens"]) == sorted(lot_body["allergens"])
    assert parse(data["pickup_start"]) == parse(lot_body["pickup_start"])
    assert parse(data["pickup_end"]) == parse(lot_body["pickup_end"])
    assert data["status"] == "available"
    assert parse(data["created_at"]).tzinfo is not None

    lot = db.get(Lot, data["id"])
    assert lot.supplier_id == supplier.id
    assert lot.remaining_quantity == lot.quantity == 30


def test_create_lot_defaults(api: httpx2.Client, supplier_headers: dict, lot_body: dict):
    """`divisible` defaults to true and `allergens` to an empty list."""
    del lot_body["divisible"], lot_body["allergens"]

    response = api.post(LOTS_PATH, json=lot_body, headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 201
    assert response.json()["divisible"] is True
    assert response.json()["allergens"] == []


def test_create_indivisible_lot(api: httpx2.Client, supplier_headers: dict, lot_body: dict):
    response = api.post(LOTS_PATH, json={**lot_body, "divisible": False}, headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 201
    assert response.json()["divisible"] is False


def test_create_lot_fractional_quantity(api: httpx2.Client, supplier_headers: dict, lot_body: dict):
    response = api.post(
        LOTS_PATH, json={**lot_body, "quantity": 2.5, "unit": "kg"}, headers=supplier_headers
    )

    assert_contract(response)
    assert response.status_code == 201
    assert response.json()["quantity"] == 2.5
    assert response.json()["remaining_quantity"] == 2.5


def test_create_lot_use_by_today(api: httpx2.Client, supplier_headers: dict, lot_body: dict):
    """The use-by date can be today, with a pickup window ending by the end of the day."""
    day = today()
    lot_body.update(
        use_by_date=day.isoformat(),
        pickup_start=iso(at(day, 0)),
        pickup_end=iso(at(day + timedelta(days=1), 0)),
    )

    response = api.post(LOTS_PATH, json=lot_body, headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 201
    assert response.json()["status"] == "available"


def test_create_lot_pickup_ends_at_end_of_use_by_day(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict
):
    use_by = today() + timedelta(days=1)
    lot_body.update(use_by_date=use_by.isoformat(), pickup_end=iso(at(use_by + timedelta(1), 0)))

    response = api.post(LOTS_PATH, json=lot_body, headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 201


def test_create_lot_with_offset_datetimes(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict
):
    """Date-times with an offset are accepted and answered in UTC."""
    tomorrow = today() + timedelta(days=1)
    lot_body.update(
        pickup_start=f"{tomorrow.isoformat()}T14:00:00+01:00",
        pickup_end=f"{tomorrow.isoformat()}T16:00:00+01:00",
    )

    response = api.post(LOTS_PATH, json=lot_body, headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 201
    assert parse(response.json()["pickup_start"]) == at(tomorrow, 13)
    assert response.json()["pickup_start"].endswith("Z")


def test_create_lot_two_suppliers(
    api: httpx2.Client, create_supplier, create_user, auth_headers, lot_body: dict
):
    """Each lot is published under the supplier of the logged-in manager."""
    other = create_supplier(name="Hôpital Édouard-Herriot", supplier_type=SupplierType.HOSPITAL)
    headers = auth_headers(create_user(email="hopital@example.org", supplier=other))

    response = api.post(LOTS_PATH, json=lot_body, headers=headers)

    assert_contract(response)
    assert response.status_code == 201
    assert_supplier_summary(response.json()["supplier"], other)


# ----- 400 -----


@pytest.mark.parametrize(
    "body",
    ["{", '{"title": "Hachis parmentier",}', "not json"],
    ids=["unclosed", "trailing-comma", "plain-text"],
)
def test_create_lot_malformed_json(client: TestClient, supplier_headers: dict, body: str, db):
    """Sent in-process: Prism never answers a malformed JSON body."""
    response = client.post(
        API_PREFIX + LOTS_PATH,
        content=body,
        headers={**supplier_headers, "Content-Type": "application/json"},
    )

    assert_error(response, 400, "bad_request")
    assert _lot_count(db) == 0


# ----- 401 -----


def test_create_lot_without_token(api: httpx2.Client, lot_body: dict, db: Session):
    response = api.post(LOTS_PATH, json=lot_body)

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert _lot_count(db) == 0


def test_create_lot_invalid_token(api: httpx2.Client, lot_body: dict):
    response = api.post(LOTS_PATH, json=lot_body, headers={"Authorization": "Bearer not-a-jwt"})

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


def test_create_lot_without_token_and_body(api: httpx2.Client):
    """Authentication is checked before the body."""
    response = api.post(LOTS_PATH, json={})

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


def test_create_lot_as_association(
    api: httpx2.Client, association_headers: dict, lot_body: dict, db: Session
):
    response = api.post(LOTS_PATH, json=lot_body, headers=association_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")
    assert _lot_count(db) == 0


def test_create_lot_as_admin(api: httpx2.Client, admin_headers: dict, lot_body: dict):
    response = api.post(LOTS_PATH, json=lot_body, headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_create_lot_manager_without_supplier(
    api: httpx2.Client, create_user, auth_headers, lot_body: dict
):
    """A manager whose registration request is not approved yet has no supplier."""
    user = create_user(registration_status=RegistrationStatus.PENDING)

    response = api.post(LOTS_PATH, json=lot_body, headers=auth_headers(user))

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_create_lot_as_association_with_invalid_body(api: httpx2.Client, association_headers: dict):
    """The role is checked before the body."""
    response = api.post(LOTS_PATH, json={}, headers=association_headers)

    assert_contract(response, invalid_request=True)
    assert_error(response, 403, "forbidden")


# ----- 422 -----


def _assert_validation_error(response, field: str, *, invalid_request: bool = True) -> None:
    """`invalid_request=False` for bodies that respect the schema but break a business rule."""
    assert_contract(response, invalid_request=invalid_request)
    data = assert_error(response, 422, "validation_error")
    assert field in [detail["field"] for detail in data["details"]]
    for detail in data["details"]:
        assert set(detail) == {"field", "message"}
        assert detail["message"]


@pytest.mark.parametrize(
    "field",
    [
        "title",
        "category",
        "quantity",
        "unit",
        "use_by_date",
        "storage",
        "pickup_start",
        "pickup_end",
    ],
)
def test_create_lot_missing_field(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict, field: str, db: Session
):
    del lot_body[field]

    response = api.post(LOTS_PATH, json=lot_body, headers=supplier_headers)

    _assert_validation_error(response, field)
    assert _lot_count(db) == 0


@pytest.mark.parametrize("quantity", [0, -5])
def test_create_lot_quantity_not_positive(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict, quantity: int, db: Session
):
    response = api.post(
        LOTS_PATH, json={**lot_body, "quantity": quantity}, headers=supplier_headers
    )

    _assert_validation_error(response, "quantity")
    assert _lot_count(db) == 0


def test_create_lot_quantity_too_precise(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict
):
    """Quantities are stored with 3 decimals: more would be silently rounded."""
    response = api.post(
        LOTS_PATH, json={**lot_body, "quantity": 1.2345, "unit": "kg"}, headers=supplier_headers
    )

    _assert_validation_error(response, "quantity", invalid_request=False)


def test_create_lot_use_by_date_passed(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict, db: Session
):
    yesterday = today() - timedelta(days=1)
    lot_body.update(
        use_by_date=yesterday.isoformat(),
        pickup_start=iso(at(yesterday, 13)),
        pickup_end=iso(at(yesterday, 15)),
    )

    response = api.post(LOTS_PATH, json=lot_body, headers=supplier_headers)

    _assert_validation_error(response, "use_by_date", invalid_request=False)
    assert _lot_count(db) == 0


@pytest.mark.parametrize("minutes", [0, -30], ids=["same-time", "before"])
def test_create_lot_pickup_ends_before_it_starts(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict, minutes: int, db: Session
):
    start = parse(lot_body["pickup_start"])
    lot_body["pickup_end"] = iso(start + timedelta(minutes=minutes))

    response = api.post(LOTS_PATH, json=lot_body, headers=supplier_headers)

    _assert_validation_error(response, "pickup_end", invalid_request=False)
    assert _lot_count(db) == 0


def test_create_lot_pickup_ends_after_use_by_day(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict, db: Session
):
    use_by = today() + timedelta(days=1)
    lot_body.update(
        use_by_date=use_by.isoformat(),
        pickup_start=iso(at(use_by, 22)),
        pickup_end=iso(at(use_by + timedelta(days=1), 0, 30)),
    )

    response = api.post(LOTS_PATH, json=lot_body, headers=supplier_headers)

    _assert_validation_error(response, "pickup_end", invalid_request=False)
    assert _lot_count(db) == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "ab"),
        ("title", "x" * 121),
        ("category", "clothes"),
        ("unit", "liters"),
        ("storage", "warm"),
        ("quantity", "thirty"),
        ("divisible", "maybe"),
        ("use_by_date", "04/11/2026"),
        ("pickup_start", "tomorrow"),
        ("allergens", "milk"),
    ],
)
def test_create_lot_invalid_field(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict, field: str, value
):
    response = api.post(LOTS_PATH, json={**lot_body, field: value}, headers=supplier_headers)

    _assert_validation_error(response, field)


def test_create_lot_unknown_allergen(api: httpx2.Client, supplier_headers: dict, lot_body: dict):
    response = api.post(
        LOTS_PATH, json={**lot_body, "allergens": ["milk", "plastic"]}, headers=supplier_headers
    )

    _assert_validation_error(response, "allergens.1")


def test_create_lot_duplicate_allergens(api: httpx2.Client, supplier_headers: dict, lot_body: dict):
    """uniqueItems: true"""
    response = api.post(
        LOTS_PATH, json={**lot_body, "allergens": ["milk", "milk"]}, headers=supplier_headers
    )

    _assert_validation_error(response, "allergens")


def test_create_lot_datetime_without_timezone(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict
):
    """A date-time without offset is ambiguous (ISO 8601 / RFC 3339 require one)."""
    tomorrow = today() + timedelta(days=1)
    response = api.post(
        LOTS_PATH,
        json={**lot_body, "pickup_start": f"{tomorrow.isoformat()}T13:00:00"},
        headers=supplier_headers,
    )

    _assert_validation_error(response, "pickup_start")


def test_create_lot_unknown_field(api: httpx2.Client, supplier_headers: dict, lot_body: dict):
    """additionalProperties: false (a client cannot set the status or the remaining quantity)."""
    response = api.post(
        LOTS_PATH, json={**lot_body, "remaining_quantity": 5}, headers=supplier_headers
    )

    _assert_validation_error(response, "remaining_quantity")


def test_create_lot_reports_every_invalid_field(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict
):
    response = api.post(
        LOTS_PATH, json={**lot_body, "title": "", "quantity": 0}, headers=supplier_headers
    )

    assert_contract(response, invalid_request=True)
    data = assert_error(response, 422, "validation_error")
    assert {"title", "quantity"} <= {detail["field"] for detail in data["details"]}


def test_create_lot_quantity_decimal_is_exact(
    api: httpx2.Client, supplier_headers: dict, lot_body: dict, db: Session
):
    response = api.post(
        LOTS_PATH, json={**lot_body, "quantity": 0.1, "unit": "kg"}, headers=supplier_headers
    )

    assert response.status_code == 201
    assert db.get(Lot, response.json()["id"]).quantity == Decimal("0.1")
