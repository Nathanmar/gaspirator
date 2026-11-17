"""POST /registration-requests: 201 `RegistrationRequest`, 400, 409 and 422 (format `Error`).

The body registers either a supplier (`supplier`, with a SIRET) or an association
(`association`, with an RNA number), with the account of its manager. Without address, it
is found from the SIRET or the RNA number (fake registry of conftest.py). The address is
geocoded (fake geocoder of conftest.py): 422 if it cannot be found, 503 (outside the
contract) if one of these services is unavailable.
"""

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import RegistrationRequest, User
from app.schemas import RegistrationStatus
from tests.conftest import REGISTRATION_URL
from tests.prism import API_PREFIX, assert_contract

REGISTRATION_PATH = REGISTRATION_URL.removeprefix(API_PREFIX)

REQUEST_FIELDS = {
    "id",
    "status",
    "supplier",
    "association",
    "account",
    "supplier_id",
    "association_id",
    "created_at",
    "decided_at",
}


def _assert_error(response, status: int, code: str) -> dict:
    assert response.status_code == status
    data = response.json()
    assert data["code"] == code
    assert isinstance(data["message"], str) and data["message"]
    return data


def _request_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(RegistrationRequest))


# ----- 201 -----


def test_register_supplier(api: httpx2.Client, registration: dict, db: Session):
    response = api.post(REGISTRATION_PATH, json=registration)

    assert_contract(response)
    assert response.status_code == 201
    data = response.json()
    assert set(data) == REQUEST_FIELDS
    assert isinstance(data["id"], int)
    assert data["status"] == "pending"
    assert data["supplier"] == registration["supplier"]
    assert data["association"] is None
    assert data["account"] == {
        "firstname": "Marie",
        "lastname": "Dupont",
        "email": "marie.dupont@example.org",
    }
    assert data["supplier_id"] is None
    assert data["association_id"] is None
    assert data["created_at"]
    assert data["decided_at"] is None

    request = db.get(RegistrationRequest, data["id"])
    assert request.status == RegistrationStatus.PENDING
    assert request.user.email == "marie.dupont@example.org"
    assert request.user.password_hash != "testPass1."


REGISTRY_ADDRESS = {"street": "40 RUE DES CHANTIERS", "postal_code": "76600", "city": "LE HAVRE"}


@pytest.mark.parametrize("omit", ["absent", "null"])
def test_register_supplier_without_address(
    api: httpx2.Client, registration: dict, registry, geocoder, db: Session, omit: str
):
    """Without address, it is found from the SIRET, geocoded, stored and answered."""
    if omit == "absent":
        del registration["supplier"]["address"]
    else:
        registration["supplier"]["address"] = None

    response = api.post(REGISTRATION_PATH, json=registration)

    assert_contract(response)
    assert response.status_code == 201
    assert response.json()["supplier"]["address"] == REGISTRY_ADDRESS
    assert registry.lookups == [("supplier", registration["supplier"]["legal_id"])]
    assert [address.model_dump() for address in geocoder.addresses] == [REGISTRY_ADDRESS]
    request = db.get(RegistrationRequest, response.json()["id"])
    assert (request.street, request.postal_code, request.city) == tuple(REGISTRY_ADDRESS.values())
    assert (request.latitude, request.longitude) == (45.76511, 4.835769)


def test_register_association_without_address(
    api: httpx2.Client, association_registration: dict, registry, db: Session
):
    """Without address, it is found from the RNA number."""
    del association_registration["association"]["address"]

    response = api.post(REGISTRATION_PATH, json=association_registration)

    assert_contract(response)
    assert response.status_code == 201
    assert response.json()["association"]["address"] == REGISTRY_ADDRESS
    assert registry.lookups == [("association", "W691234567")]
    assert db.get(RegistrationRequest, response.json()["id"]).latitude is not None


def test_register_with_address_is_not_looked_up(api: httpx2.Client, registration: dict, registry):
    """The address given wins: the Sirene base is not queried."""
    response = api.post(REGISTRATION_PATH, json=registration)

    assert response.status_code == 201
    assert response.json()["supplier"]["address"] == registration["supplier"]["address"]
    assert registry.lookups == []


def test_register_association(api: httpx2.Client, association_registration: dict):
    response = api.post(REGISTRATION_PATH, json=association_registration)

    assert_contract(response)
    assert response.status_code == 201
    data = response.json()
    assert set(data) == REQUEST_FIELDS
    assert data["supplier"] is None
    assert data["association"] == association_registration["association"]
    assert data["account"]["email"] == "paul.martin@example.org"
    assert data["supplier_id"] is None
    assert data["association_id"] is None


def test_register_geocodes_the_address(
    api: httpx2.Client, registration: dict, geocoder, db: Session
):
    """The address is geocoded when the request is sent; the position is kept with it."""
    response = api.post(REGISTRATION_PATH, json=registration)

    assert_contract(response)
    assert response.status_code == 201
    assert [address.model_dump() for address in geocoder.addresses] == [
        registration["supplier"]["address"]
    ]
    request = db.get(RegistrationRequest, response.json()["id"])
    assert (request.latitude, request.longitude) == (45.76511, 4.835769)


def test_register_association_geocodes_the_address(
    api: httpx2.Client, association_registration: dict, geocoder, db: Session
):
    response = api.post(REGISTRATION_PATH, json=association_registration)

    assert response.status_code == 201
    assert [address.model_dump() for address in geocoder.addresses] == [
        association_registration["association"]["address"]
    ]
    request = db.get(RegistrationRequest, response.json()["id"])
    assert request.latitude is not None and request.longitude is not None


def test_register_does_not_create_the_supplier_yet(api: httpx2.Client, registration: dict, db):
    """The supplier is created when an admin approves the request; the user has none."""
    response = api.post(REGISTRATION_PATH, json=registration)

    user = db.scalar(select(User))
    assert response.status_code == 201
    assert user.supplier_id is None and user.association_id is None


# ----- 400 -----


@pytest.mark.parametrize(
    "body",
    [
        "{",
        '{"supplier": {"name": "Cantine"},}',
        '{"account": {"email": "marie.dupont@example.org" "password": "testPass1."}}',
        "{'supplier': {}, 'account': {}}",
        "not json",
    ],
    ids=["unclosed", "trailing-comma", "missing-comma", "single-quotes", "plain-text"],
)
def test_register_malformed_json(client: TestClient, body: str, db: Session):
    """Sent in-process: Prism never answers a malformed JSON body."""
    response = client.post(
        REGISTRATION_URL, content=body, headers={"Content-Type": "application/json"}
    )

    _assert_error(response, 400, "bad_request")
    assert _request_count(db) == 0


# ----- 409 -----


def test_register_email_already_used(
    api: httpx2.Client, registration: dict, association_registration: dict, db: Session
):
    """Same e-mail (any case), whether for a supplier or an association: 409."""
    assert api.post(REGISTRATION_PATH, json=registration).status_code == 201
    association_registration["account"]["email"] = "Marie.Dupont@Example.org"

    response = api.post(REGISTRATION_PATH, json=association_registration)

    assert_contract(response)
    _assert_error(response, 409, "conflict")
    assert _request_count(db) == 1


def test_register_conflict_is_not_geocoded(api: httpx2.Client, registration: dict, geocoder):
    """The conflicts are checked first: no call to the geocoding service for nothing."""
    api.post(REGISTRATION_PATH, json=registration)
    geocoder.addresses.clear()

    response = api.post(REGISTRATION_PATH, json=registration)

    assert response.status_code == 409
    assert geocoder.addresses == []


def test_register_siret_already_used(api: httpx2.Client, registration: dict, db: Session):
    assert api.post(REGISTRATION_PATH, json=registration).status_code == 201
    registration["account"]["email"] = "autre@example.org"

    response = api.post(REGISTRATION_PATH, json=registration)

    assert_contract(response)
    _assert_error(response, 409, "conflict")
    assert _request_count(db) == 1


def test_register_rna_already_used(api: httpx2.Client, association_registration: dict):
    assert api.post(REGISTRATION_PATH, json=association_registration).status_code == 201
    association_registration["account"]["email"] = "autre@example.org"

    response = api.post(REGISTRATION_PATH, json=association_registration)

    assert_contract(response)
    _assert_error(response, 409, "conflict")


def test_register_siret_of_an_existing_supplier(
    api: httpx2.Client, registration: dict, create_supplier
):
    create_supplier(legal_id=registration["supplier"]["legal_id"])

    response = api.post(REGISTRATION_PATH, json=registration)

    assert_contract(response)
    _assert_error(response, 409, "conflict")


def test_register_rna_of_an_existing_association(
    api: httpx2.Client, association_registration: dict, create_association
):
    create_association(legal_id=association_registration["association"]["legal_id"])

    response = api.post(REGISTRATION_PATH, json=association_registration)

    assert_contract(response)
    _assert_error(response, 409, "conflict")


# ----- 422 -----


def _assert_validation_error(response, field: str) -> None:
    assert_contract(response, invalid_request=True)
    data = _assert_error(response, 422, "validation_error")
    assert field in [detail["field"] for detail in data["details"]]
    for detail in data["details"]:
        assert set(detail) == {"field", "message"}
        assert detail["message"]


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("account", "email", "invalid-email"),
        ("account", "password", "weak"),
        ("account", "firstname", ""),
        ("supplier", "name", "A"),
        ("supplier", "legal_id", "123456789"),
        ("supplier", "legal_id", "W691234567"),
        ("supplier", "supplier_type", "restaurant"),
        ("supplier", "supplier_type", None),
        ("supplier", "contact_phone", "555-1234"),
    ],
)
def test_register_supplier_invalid_field(
    api: httpx2.Client, registration: dict, section: str, field: str, value, db: Session
):
    registration[section][field] = value

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_validation_error(response, f"{section}.{field}")
    assert _request_count(db) == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [("name", "A"), ("legal_id", "19690103400017"), ("legal_id", "W12"), ("contact_phone", "1")],
)
def test_register_association_invalid_field(
    api: httpx2.Client, association_registration: dict, field: str, value: str
):
    association_registration["association"][field] = value

    response = api.post(REGISTRATION_PATH, json=association_registration)

    _assert_validation_error(response, f"association.{field}")


def test_register_association_with_supplier_type(
    api: httpx2.Client, association_registration: dict
):
    """An association has no type of establishment (additionalProperties: false)."""
    association_registration["association"]["supplier_type"] = "canteen"

    response = api.post(REGISTRATION_PATH, json=association_registration)

    _assert_validation_error(response, "association.supplier_type")


def test_register_invalid_postal_code(api: httpx2.Client, registration: dict):
    registration["supplier"]["address"]["postal_code"] = "6900"

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_validation_error(response, "supplier.address.postal_code")


@pytest.mark.parametrize("field", ["firstname", "lastname", "email", "password"])
def test_register_missing_account_field(api: httpx2.Client, registration: dict, field: str):
    del registration["account"][field]

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_validation_error(response, f"account.{field}")


@pytest.mark.parametrize("field", ["name", "legal_id", "supplier_type", "contact_phone"])
def test_register_missing_supplier_field(api: httpx2.Client, registration: dict, field: str):
    del registration["supplier"][field]

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_validation_error(response, f"supplier.{field}")


def test_register_missing_account(api: httpx2.Client, registration: dict):
    del registration["account"]

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_validation_error(response, "account")


def test_register_neither_supplier_nor_association(api: httpx2.Client, registration: dict):
    del registration["supplier"]

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_validation_error(response, "supplier")


def test_register_both_supplier_and_association(
    api: httpx2.Client, registration: dict, association_registration: dict, db: Session
):
    registration["association"] = association_registration["association"]

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_validation_error(response, "association")
    assert _request_count(db) == 0


def test_register_former_organization_format(api: httpx2.Client, registration: dict):
    """The `organization` object of the previous contract is no longer accepted."""
    registration["organization"] = {**registration.pop("supplier"), "type": "supplier"}

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_validation_error(response, "organization")


def test_register_unknown_field(api: httpx2.Client, registration: dict):
    """additionalProperties: false"""
    registration["supplier"]["opening_hours"] = "9h-17h"

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_validation_error(response, "supplier.opening_hours")


def test_register_invalid_body_is_not_geocoded(api: httpx2.Client, registration: dict, geocoder):
    registration["account"]["email"] = "invalid-email"

    response = api.post(REGISTRATION_PATH, json=registration)

    assert response.status_code == 422
    assert geocoder.addresses == []


# ----- 422: address not found -----


def _assert_address_not_found(response, field: str) -> None:
    """The body respects the schema: only the response is out of the ordinary."""
    assert_contract(response)
    data = _assert_error(response, 422, "validation_error")
    assert data["details"] == [{"field": field, "message": "adresse introuvable"}]


def test_register_supplier_address_not_found(
    api: httpx2.Client, registration: dict, geocoder, db: Session
):
    geocoder.point = None

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_address_not_found(response, "supplier.address")
    assert _request_count(db) == 0
    assert db.scalar(select(func.count()).select_from(User)) == 0


def test_register_association_address_not_found(
    api: httpx2.Client, association_registration: dict, geocoder, db: Session
):
    geocoder.point = None

    response = api.post(REGISTRATION_PATH, json=association_registration)

    _assert_address_not_found(response, "association.address")
    assert _request_count(db) == 0


@pytest.mark.parametrize(
    ("section", "message"),
    [
        ("supplier", "obligatoire : introuvable à partir du SIRET"),
        ("association", "obligatoire : introuvable à partir du n° RNA"),
    ],
)
def test_register_without_address_not_in_registry(
    api: httpx2.Client,
    registration: dict,
    association_registration: dict,
    registry,
    geocoder,
    db: Session,
    section: str,
    message: str,
):
    """No usable address in the Sirene base (unknown, not public...): it must be sent."""
    body = registration if section == "supplier" else association_registration
    del body[section]["address"]
    registry.address = None

    response = api.post(REGISTRATION_PATH, json=body)

    assert_contract(response)
    data = _assert_error(response, 422, "validation_error")
    assert data["details"] == [{"field": f"{section}.address", "message": message}]
    assert geocoder.addresses == []
    assert _request_count(db) == 0


def test_register_registry_address_not_geocoded(
    api: httpx2.Client, registration: dict, geocoder, db: Session
):
    """The address found from the SIRET is geocoded like any other."""
    del registration["supplier"]["address"]
    geocoder.point = None

    response = api.post(REGISTRATION_PATH, json=registration)

    _assert_address_not_found(response, "supplier.address")
    assert _request_count(db) == 0


def test_register_conflict_is_not_looked_up(api: httpx2.Client, registration: dict, registry):
    api.post(REGISTRATION_PATH, json=registration)
    del registration["supplier"]["address"]

    response = api.post(REGISTRATION_PATH, json=registration)

    assert response.status_code == 409
    assert registry.lookups == []


def test_register_invalid_body_is_not_looked_up(api: httpx2.Client, registration: dict, registry):
    del registration["supplier"]["address"]
    registration["account"]["email"] = "invalid-email"

    response = api.post(REGISTRATION_PATH, json=registration)

    assert response.status_code == 422
    assert registry.lookups == []


# ----- 503: external service unavailable (not in the contract) -----


def test_register_registry_unavailable(
    client: TestClient, registration: dict, registry, db: Session
):
    """Sent in-process: the contract has no response for it, Prism would report it."""
    del registration["supplier"]["address"]
    registry.unavailable = True

    response = client.post(REGISTRATION_URL, json=registration)

    _assert_error(response, 503, "service_unavailable")
    assert int(response.headers["Retry-After"]) > 0
    assert _request_count(db) == 0


def test_register_geocoding_unavailable(
    client: TestClient, registration: dict, geocoder, db: Session
):
    """Nothing the applicant can fix: 503, retry later, nothing is stored.

    Sent in-process: the contract has no response for it, Prism would report it.
    """
    geocoder.unavailable = True

    response = client.post(REGISTRATION_URL, json=registration)

    _assert_error(response, 503, "service_unavailable")
    assert int(response.headers["Retry-After"]) > 0
    assert _request_count(db) == 0
