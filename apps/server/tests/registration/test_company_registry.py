"""`RechercheEntreprisesRegistry`: address of a supplier (SIRET) or an association (RNA
number) in the Sirene base, through the API Recherche d'entreprises
(https://recherche-entreprises.api.gouv.fr), here replaced by a local HTTP server."""

import pytest

from app.company_registry import RechercheEntreprisesRegistry, RegistryUnavailable
from app.schemas import Address
from tests.http_stub import stub_api

SIRET = "39417174800103"
RNA = "W762000965"
ADDRESS = Address(street="40 RUE DES CHANTIERS", postal_code="76600", city="LE HAVRE")


def _establishment(siret: str = SIRET, **fields) -> dict:
    """An establishment as the API describes it (`siege`, `matching_etablissements`)."""
    return {
        "siret": siret,
        "adresse": "40 RUE DES CHANTIERS 76600 LE HAVRE",
        "numero_voie": "40",
        "indice_repetition": None,
        "type_voie": "RUE",
        "libelle_voie": "DES CHANTIERS",
        "complement_adresse": None,
        "code_postal": "76600",
        "libelle_commune": "LE HAVRE",
        "latitude": "49.4777752659864",
        "longitude": "0.160208344019971",
        "etat_administratif": "A",
        "est_siege": True,
        **fields,
    }


def _result(rna: str | None = RNA, siege: dict | None = None, matching=None) -> dict:
    """A legal unit with its head office and the establishments matching the search."""
    siege = siege or _establishment()
    return {
        "siren": SIRET[:9],
        "nom_complet": "RESTAURANTS DU COEUR",
        "siege": siege,
        "matching_etablissements": [siege] if matching is None else matching,
        "complements": {"identifiant_association": rna},
    }


def _results(*results: dict) -> dict:
    return {"results": list(results), "total_results": len(results), "page": 1}


@pytest.fixture
def stub():
    """A local API Recherche d'entreprises (no result by default)."""
    with stub_api() as (state, url):
        state.answer_json(_results())
        yield state, url


# ----- Suppliers (SIRET) -----


def test_supplier_address(stub):
    state, url = stub
    state.answer_json(_results(_result()))

    assert RechercheEntreprisesRegistry(url).supplier_address(SIRET) == ADDRESS


def test_supplier_query(stub):
    """A direct search on the SIRET, with an explicit User-Agent (asked by the API)."""
    state, url = stub
    state.answer_json(_results(_result()))

    RechercheEntreprisesRegistry(url).supplier_address(SIRET)

    path, query, headers = state.last_request
    assert path == "/search"
    assert query["q"] == [SIRET]
    assert headers["User-Agent"].startswith("gaspirator")


def _matching_establishment(siret: str, adresse: str, code_postal: str, city: str) -> dict:
    """A `matching_etablissements` entry: the address only as a whole (`adresse`), without
    the street number, type and name of the head office."""
    return {
        "siret": siret,
        "adresse": adresse,
        "code_postal": code_postal,
        "libelle_commune": city,
        "etat_administratif": "A",
        "est_siege": False,
    }


def test_supplier_address_of_the_matching_establishment(stub):
    """The address is the one of the establishment of this SIRET, not of the head office."""
    state, url = stub
    shop = _matching_establishment("39417174800111", "3 AV FOCH 69006 LYON", "69006", "LYON")
    state.answer_json(_results(_result(matching=[shop])))

    address = RechercheEntreprisesRegistry(url).supplier_address("39417174800111")

    assert address == Address(street="3 AV FOCH", postal_code="69006", city="LYON")


def test_supplier_address_of_the_head_office_as_matched(stub):
    """The real answer for a head office SIRET: `matching_etablissements` without the
    street fields."""
    state, url = stub
    matched = _matching_establishment(
        SIRET, "40 RUE DES CHANTIERS 76600 LE HAVRE", "76600", "LE HAVRE"
    )
    state.answer_json(_results(_result(matching=[matched])))

    assert RechercheEntreprisesRegistry(url).supplier_address(SIRET) == ADDRESS


def test_supplier_address_whole_without_city_suffix(stub):
    """An `adresse` that does not end with the postal code and city cannot be split."""
    state, url = stub
    matched = _matching_establishment(SIRET, "40 RUE DES CHANTIERS", "76600", "LE HAVRE")
    state.answer_json(_results(_result(matching=[matched])))

    assert RechercheEntreprisesRegistry(url).supplier_address(SIRET) is None


def test_supplier_address_with_repetition_index(stub):
    state, url = stub
    state.answer_json(_results(_result(siege=_establishment(indice_repetition="B"))))

    address = RechercheEntreprisesRegistry(url).supplier_address(SIRET)

    assert address.street == "40 B RUE DES CHANTIERS"


def test_supplier_address_without_street_number(stub):
    state, url = stub
    state.answer_json(_results(_result(siege=_establishment(numero_voie=None))))

    assert RechercheEntreprisesRegistry(url).supplier_address(SIRET).street == "RUE DES CHANTIERS"


def test_supplier_unknown_siret(stub):
    _, url = stub

    assert RechercheEntreprisesRegistry(url).supplier_address(SIRET) is None


def test_supplier_siret_of_another_establishment(stub):
    state, url = stub
    state.answer_json(_results(_result()))

    assert RechercheEntreprisesRegistry(url).supplier_address("39417174800999") is None


@pytest.mark.parametrize(
    "fields",
    [
        {"code_postal": None},
        {"libelle_commune": None},
        {"numero_voie": None, "type_voie": None, "libelle_voie": None, "adresse": None},
        {"code_postal": "[ND]", "libelle_commune": "[NON-DIFFUSIBLE]"},
    ],
    ids=["no-postal-code", "no-city", "no-street", "not-public"],
)
def test_supplier_address_incomplete(stub, fields: dict):
    """No usable address (missing, or not public): the applicant has to give it."""
    state, url = stub
    state.answer_json(_results(_result(siege=_establishment(**fields))))

    assert RechercheEntreprisesRegistry(url).supplier_address(SIRET) is None


# ----- Associations (RNA number) -----


def test_association_address(stub):
    """The address of the head office of the association with this RNA number."""
    state, url = stub
    state.answer_json(_results(_result()))

    address = RechercheEntreprisesRegistry(url).association_address(RNA)

    assert address == ADDRESS
    _, query, _ = state.last_request
    assert query["q"] == [RNA]


def test_association_unknown_rna(stub):
    """An association with an RNA number only (no SIREN) is not in the Sirene base."""
    _, url = stub

    assert RechercheEntreprisesRegistry(url).association_address(RNA) is None


def test_association_result_with_another_rna(stub):
    """The text search may match something else: only this RNA number counts."""
    state, url = stub
    state.answer_json(_results(_result(rna="W543001502"), _result(rna=None)))

    assert RechercheEntreprisesRegistry(url).association_address(RNA) is None


# ----- Service unavailable -----


@pytest.mark.parametrize("status", [400, 429, 500, 503])
def test_service_error(stub, status: int):
    state, url = stub
    state.status = status

    with pytest.raises(RegistryUnavailable):
        RechercheEntreprisesRegistry(url).supplier_address(SIRET)


@pytest.mark.parametrize(
    "body", [b"<html>maintenance</html>", b'{"results": "none"}', b'{"results": [{}]}']
)
def test_unexpected_answer(stub, body: bytes):
    state, url = stub
    state.body = body

    with pytest.raises(RegistryUnavailable):
        RechercheEntreprisesRegistry(url).association_address(RNA)


def test_service_unreachable():
    with pytest.raises(RegistryUnavailable):
        RechercheEntreprisesRegistry("http://127.0.0.1:9", timeout=1).supplier_address(SIRET)
