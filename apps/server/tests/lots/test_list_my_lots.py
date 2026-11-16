"""GET /me/lots: 200 `LotPage`, 401 and 403 (format `Error`). Suppliers only.

The lots of the current supplier, whatever their status, most recent first.
"""

from datetime import UTC, datetime, timedelta

import httpx2
import pytest
from fastapi.testclient import TestClient

from app.schemas import RegistrationStatus, SupplierType
from tests.lots.helpers import LOT_FIELDS, assert_error, assert_supplier_summary
from tests.prism import API_PREFIX, assert_contract

MY_LOTS_PATH = "/me/lots"


def _created_lots(create_lot, count: int) -> list:
    """`count` lots created one hour apart, oldest first."""
    start = datetime.now(UTC) - timedelta(days=1)
    return [
        create_lot(title=f"Lot {index}", created_at=start + timedelta(hours=index))
        for index in range(count)
    ]


def _ids(response) -> list[int]:
    return [lot["id"] for lot in response.json()["data"]]


# ----- 200 -----


def test_list_my_lots(api: httpx2.Client, supplier_headers: dict, supplier, create_lot):
    lot = create_lot()

    response = api.get(MY_LOTS_PATH, headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"data", "meta"}
    assert data["meta"] == {"page": 1, "per_page": 20, "total": 1}
    [item] = data["data"]
    assert set(item) == LOT_FIELDS
    assert item["id"] == lot.id
    assert_supplier_summary(item["supplier"], supplier)
    assert item["status"] == "available"


def test_list_my_lots_empty(api: httpx2.Client, supplier_headers: dict):
    response = api.get(MY_LOTS_PATH, headers=supplier_headers)

    assert_contract(response)
    assert response.status_code == 200
    assert response.json() == {"data": [], "meta": {"page": 1, "per_page": 20, "total": 0}}


def test_list_my_lots_most_recent_first(api: httpx2.Client, supplier_headers: dict, create_lot):
    lots = _created_lots(create_lot, 3)

    response = api.get(MY_LOTS_PATH, headers=supplier_headers)

    assert_contract(response)
    assert _ids(response) == [lot.id for lot in reversed(lots)]


def test_list_my_lots_same_creation_time(api: httpx2.Client, supplier_headers: dict, create_lot):
    """Lots created at the same time keep a stable order: the last inserted first."""
    created_at = datetime.now(UTC) - timedelta(hours=1)
    lots = [create_lot(created_at=created_at) for _ in range(3)]

    response = api.get(MY_LOTS_PATH, headers=supplier_headers)

    assert _ids(response) == [lot.id for lot in reversed(lots)]


def test_list_my_lots_only_mine(
    api: httpx2.Client, supplier_headers: dict, create_lot, create_supplier
):
    mine = create_lot()
    other = create_supplier(name="Hôpital Édouard-Herriot", supplier_type=SupplierType.HOSPITAL)
    create_lot(supplier=other)

    response = api.get(MY_LOTS_PATH, headers=supplier_headers)

    assert_contract(response)
    assert _ids(response) == [mine.id]
    assert response.json()["meta"]["total"] == 1


def test_list_my_lots_every_status(api: httpx2.Client, supplier_headers: dict, create_lot):
    """The supplier also sees the lots that are no longer available."""
    now = datetime.now(UTC)
    create_lot(created_at=now - timedelta(hours=3))
    create_lot(quantity=10, remaining_quantity=0, created_at=now - timedelta(hours=2))
    create_lot(
        pickup_start=now - timedelta(hours=3),
        pickup_end=now - timedelta(hours=1),
        created_at=now - timedelta(hours=1),
    )

    response = api.get(MY_LOTS_PATH, headers=supplier_headers)

    assert_contract(response)
    assert [lot["status"] for lot in response.json()["data"]] == [
        "expired",
        "reserved",
        "available",
    ]


def test_list_my_lots_after_creation(api: httpx2.Client, supplier_headers: dict, lot_body: dict):
    created = api.post("/lots", json=lot_body, headers=supplier_headers).json()

    response = api.get(MY_LOTS_PATH, headers=supplier_headers)

    assert_contract(response)
    assert response.json()["data"] == [created]


# ----- 200: pagination -----


def test_list_my_lots_pages(api: httpx2.Client, supplier_headers: dict, create_lot):
    lots = list(reversed(_created_lots(create_lot, 5)))  # most recent first

    first = api.get(MY_LOTS_PATH, params={"per_page": 2}, headers=supplier_headers)
    second = api.get(MY_LOTS_PATH, params={"page": 2, "per_page": 2}, headers=supplier_headers)
    last = api.get(MY_LOTS_PATH, params={"page": 3, "per_page": 2}, headers=supplier_headers)

    for response in (first, second, last):
        assert_contract(response)
        assert response.status_code == 200
    assert _ids(first) == [lot.id for lot in lots[0:2]]
    assert _ids(second) == [lot.id for lot in lots[2:4]]
    assert _ids(last) == [lots[4].id]
    assert second.json()["meta"] == {"page": 2, "per_page": 2, "total": 5}


def test_list_my_lots_page_after_the_last(api: httpx2.Client, supplier_headers: dict, create_lot):
    create_lot()

    response = api.get(MY_LOTS_PATH, params={"page": 3}, headers=supplier_headers)

    assert_contract(response)
    assert response.json() == {"data": [], "meta": {"page": 3, "per_page": 20, "total": 1}}


def test_list_my_lots_huge_page(api: httpx2.Client, supplier_headers: dict, create_lot):
    """No maximum page in the contract: a page far beyond the last one is just empty."""
    create_lot()

    response = api.get(MY_LOTS_PATH, params={"page": 10**12}, headers=supplier_headers)

    assert_contract(response)
    assert response.json()["data"] == []


def test_list_my_lots_default_page_size(api: httpx2.Client, supplier_headers: dict, create_lot):
    _created_lots(create_lot, 21)

    response = api.get(MY_LOTS_PATH, headers=supplier_headers)

    assert_contract(response)
    assert len(response.json()["data"]) == 20
    assert response.json()["meta"]["total"] == 21


def test_list_my_lots_max_page_size(api: httpx2.Client, supplier_headers: dict, create_lot):
    _created_lots(create_lot, 3)

    response = api.get(MY_LOTS_PATH, params={"per_page": 100}, headers=supplier_headers)

    assert_contract(response)
    assert response.json()["meta"]["per_page"] == 100
    assert len(response.json()["data"]) == 3


@pytest.mark.parametrize(
    "params",
    [{"page": 0}, {"page": -1}, {"page": "abc"}, {"per_page": 0}, {"per_page": 101}],
    ids=["page-0", "page-negative", "page-text", "per-page-0", "per-page-101"],
)
def test_list_my_lots_invalid_pagination(client: TestClient, supplier_headers: dict, params):
    """The contract lists no 400 here, but `BadRequest` covers an incorrect parameter.

    Sent in-process: through Prism, the undocumented status would be a violation.
    """
    response = client.get(API_PREFIX + MY_LOTS_PATH, params=params, headers=supplier_headers)

    data = assert_error(response, 400, "bad_request")
    assert {detail["field"] for detail in data["details"]} <= {"page", "per_page"}


# ----- 401 -----


def test_list_my_lots_without_token(api: httpx2.Client):
    response = api.get(MY_LOTS_PATH)

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_list_my_lots_invalid_token(api: httpx2.Client):
    response = api.get(MY_LOTS_PATH, headers={"Authorization": "Bearer not-a-jwt"})

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


def test_list_my_lots_as_association(api: httpx2.Client, association_headers: dict):
    response = api.get(MY_LOTS_PATH, headers=association_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_list_my_lots_as_admin(api: httpx2.Client, admin_headers: dict):
    response = api.get(MY_LOTS_PATH, headers=admin_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_list_my_lots_manager_without_supplier(api: httpx2.Client, create_user, auth_headers):
    user = create_user(registration_status=RegistrationStatus.PENDING)

    response = api.get(MY_LOTS_PATH, headers=auth_headers(user))

    assert_contract(response)
    assert_error(response, 403, "forbidden")


def test_list_my_lots_as_association_with_invalid_pagination(
    client: TestClient, association_headers: dict
):
    """The role is checked before the parameters."""
    response = client.get(
        API_PREFIX + MY_LOTS_PATH, params={"page": 0}, headers=association_headers
    )

    assert_error(response, 403, "forbidden")
