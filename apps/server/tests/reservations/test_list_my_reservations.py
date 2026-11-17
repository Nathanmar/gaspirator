"""GET /me/reservations: 200 `ReservationPage`, 401 and 403 (format `Error`). Associations
only.

The reservations of the current association, most recent first, with their pickup codes.
"""

from datetime import UTC, datetime, timedelta

import httpx2
import pytest
from fastapi.testclient import TestClient

from app.schemas import RegistrationStatus, ReservationStatus
from tests.lots.helpers import assert_error, iso, parse
from tests.prism import API_PREFIX, assert_contract
from tests.reservations.helpers import (
    RESERVATION_FIELDS,
    assert_association_summary,
    assert_lot_summary,
    reservations_path,
)

MY_RESERVATIONS_PATH = "/me/reservations"


def _created_reservations(create_lot, association, create_reservation, count: int) -> list:
    """`count` reservations of one lot, created one hour apart, oldest first."""
    lot = create_lot(quantity=count)
    start = datetime.now(UTC) - timedelta(days=1)
    return [
        create_reservation(lot, association, quantity=1, created_at=start + timedelta(hours=index))
        for index in range(count)
    ]


def _ids(response) -> list[int]:
    return [reservation["id"] for reservation in response.json()["data"]]


# ----- 200 -----


def test_list_my_reservations(
    api: httpx2.Client, association_headers: dict, association, create_lot, create_reservation
):
    lot = create_lot()
    reservation = create_reservation(lot, association, quantity=12)

    response = api.get(MY_RESERVATIONS_PATH, headers=association_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"] == {"page": 1, "per_page": 20, "total": 1}
    [item] = data["data"]
    assert set(item) == RESERVATION_FIELDS | {"pickup_code"}
    assert item["id"] == reservation.id
    assert_lot_summary(item["lot"], lot)
    assert_association_summary(item["association"], association)
    assert item["quantity"] == 12
    assert parse(item["pickup_at"]) == reservation.pickup_at
    assert item["status"] == "booked"
    assert item["pickup_code"] == reservation.pickup_code
    assert item["collected_at"] is None


def test_list_my_reservations_empty(api: httpx2.Client, association_headers: dict):
    response = api.get(MY_RESERVATIONS_PATH, headers=association_headers)

    assert_contract(response)
    assert response.json() == {"data": [], "meta": {"page": 1, "per_page": 20, "total": 0}}


def test_list_my_reservations_most_recent_first(
    api: httpx2.Client, association_headers: dict, association, create_lot, create_reservation
):
    reservations = _created_reservations(create_lot, association, create_reservation, 3)

    response = api.get(MY_RESERVATIONS_PATH, headers=association_headers)

    assert_contract(response)
    assert _ids(response) == [reservation.id for reservation in reversed(reservations)]


def test_list_my_reservations_only_mine(
    api: httpx2.Client,
    association_headers: dict,
    association,
    create_association,
    create_lot,
    create_reservation,
):
    lot = create_lot()
    mine = create_reservation(lot, association)
    create_reservation(lot, create_association(name="Secours populaire"))

    response = api.get(MY_RESERVATIONS_PATH, headers=association_headers)

    assert_contract(response)
    assert _ids(response) == [mine.id]
    assert response.json()["meta"]["total"] == 1


def test_list_my_reservations_of_several_lots(
    api: httpx2.Client,
    association_headers: dict,
    association,
    create_lot,
    create_reservation,
):
    first = create_reservation(create_lot(), association)
    second = create_reservation(create_lot(title="Yaourts nature"), association)

    response = api.get(MY_RESERVATIONS_PATH, headers=association_headers)

    assert_contract(response)
    assert _ids(response) == [second.id, first.id]
    assert [item["lot"]["title"] for item in response.json()["data"]] == [
        "Yaourts nature",
        "Hachis parmentier",
    ]


def test_list_my_reservations_collected(
    api: httpx2.Client, association_headers: dict, association, create_lot, create_reservation
):
    """Collected reservations stay listed, with their pickup code."""
    collected_at = datetime.now(UTC).replace(microsecond=0)
    reservation = create_reservation(
        create_lot(), association, status=ReservationStatus.COLLECTED, collected_at=collected_at
    )

    response = api.get(MY_RESERVATIONS_PATH, headers=association_headers)

    assert_contract(response)
    [item] = response.json()["data"]
    assert item["status"] == "collected"
    assert parse(item["collected_at"]) == collected_at
    assert item["pickup_code"] == reservation.pickup_code


def test_list_my_reservations_after_reservation(
    api: httpx2.Client, association_headers: dict, create_lot
):
    lot = create_lot()
    created = api.post(
        reservations_path(lot.id),
        json={"quantity": 12, "pickup_at": iso(lot.pickup_start + timedelta(minutes=30))},
        headers=association_headers,
    ).json()

    response = api.get(MY_RESERVATIONS_PATH, headers=association_headers)

    assert_contract(response)
    assert response.json()["data"] == [created]


# ----- 200: pagination -----


def test_list_my_reservations_pages(
    api: httpx2.Client, association_headers: dict, association, create_lot, create_reservation
):
    reservations = list(
        reversed(_created_reservations(create_lot, association, create_reservation, 5))
    )  # most recent first

    def page(**params):
        return api.get(MY_RESERVATIONS_PATH, params=params, headers=association_headers)

    first, second, last = page(per_page=2), page(page=2, per_page=2), page(page=3, per_page=2)

    for response in (first, second, last):
        assert_contract(response)
        assert response.status_code == 200
    assert _ids(first) == [reservation.id for reservation in reservations[0:2]]
    assert _ids(second) == [reservation.id for reservation in reservations[2:4]]
    assert _ids(last) == [reservations[4].id]
    assert second.json()["meta"] == {"page": 2, "per_page": 2, "total": 5}


def test_list_my_reservations_page_after_the_last(
    api: httpx2.Client, association_headers: dict, association, create_lot, create_reservation
):
    create_reservation(create_lot(), association)

    response = api.get(MY_RESERVATIONS_PATH, params={"page": 3}, headers=association_headers)

    assert_contract(response)
    assert response.json() == {"data": [], "meta": {"page": 3, "per_page": 20, "total": 1}}


def test_list_my_reservations_huge_page(
    api: httpx2.Client, association_headers: dict, association, create_lot, create_reservation
):
    """No maximum page in the contract: a page far beyond the last one is just empty."""
    create_reservation(create_lot(), association)

    response = api.get(MY_RESERVATIONS_PATH, params={"page": 10**12}, headers=association_headers)

    assert_contract(response)
    assert response.json()["data"] == []


def test_list_my_reservations_default_page_size(
    api: httpx2.Client, association_headers: dict, association, create_lot, create_reservation
):
    _created_reservations(create_lot, association, create_reservation, 21)

    response = api.get(MY_RESERVATIONS_PATH, headers=association_headers)

    assert_contract(response)
    assert len(response.json()["data"]) == 20
    assert response.json()["meta"]["total"] == 21


def test_list_my_reservations_max_page_size(
    api: httpx2.Client, association_headers: dict, association, create_lot, create_reservation
):
    _created_reservations(create_lot, association, create_reservation, 3)

    response = api.get(MY_RESERVATIONS_PATH, params={"per_page": 100}, headers=association_headers)

    assert_contract(response)
    assert response.json()["meta"]["per_page"] == 100
    assert len(response.json()["data"]) == 3


@pytest.mark.parametrize(
    "params",
    [{"page": 0}, {"page": -1}, {"page": "abc"}, {"per_page": 0}, {"per_page": 101}],
    ids=["page-0", "page-negative", "page-text", "per-page-0", "per-page-101"],
)
def test_list_my_reservations_invalid_pagination(
    client: TestClient, association_headers: dict, params
):
    """The contract lists no 400 here, but `BadRequest` covers an incorrect parameter.

    Sent in-process: through Prism, the undocumented status would be a violation.
    """
    response = client.get(
        API_PREFIX + MY_RESERVATIONS_PATH, params=params, headers=association_headers
    )

    data = assert_error(response, 400, "bad_request")
    assert {detail["field"] for detail in data["details"]} <= {"page", "per_page"}


# ----- 401 -----


def test_list_my_reservations_without_token(api: httpx2.Client):
    response = api.get(MY_RESERVATIONS_PATH)

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_list_my_reservations_invalid_token(api: httpx2.Client):
    response = api.get(MY_RESERVATIONS_PATH, headers={"Authorization": "Bearer not-a-jwt"})

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


def test_list_my_reservations_as_supplier(api: httpx2.Client, supplier_headers: dict):
    response = api.get(MY_RESERVATIONS_PATH, headers=supplier_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_list_my_reservations_as_admin(api: httpx2.Client, admin_headers: dict):
    response = api.get(MY_RESERVATIONS_PATH, headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_list_my_reservations_manager_without_association(
    api: httpx2.Client, create_user, auth_headers
):
    user = create_user(registration_status=RegistrationStatus.PENDING)

    response = api.get(MY_RESERVATIONS_PATH, headers=auth_headers(user))

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_list_my_reservations_as_supplier_with_invalid_pagination(
    client: TestClient, supplier_headers: dict
):
    """The role is checked before the parameters."""
    response = client.get(
        API_PREFIX + MY_RESERVATIONS_PATH, params={"page": 0}, headers=supplier_headers
    )

    assert_error(response, 403, "forbidden")
