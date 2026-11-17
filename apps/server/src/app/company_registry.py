"""Address of a supplier (SIRET) or an association (RNA number) in the Sirene base, for the
registration requests sent without address (US-01).

API Recherche d'entreprises: https://recherche-entreprises.api.gouv.fr (free, no key, at
most 7 requests per second). Associations that only have an RNA number (no SIREN) are not
in the Sirene base: their manager has to give the address.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Protocol

from pydantic import ValidationError

from app.schemas import Address
from app.settings import get_settings

# The API asks for an explicit User-Agent.
USER_AGENT = "gaspirator (registration requests)"


class RegistryUnavailable(Exception):
    """The API could not be reached or gave an unexpected answer."""


class CompanyRegistry(Protocol):
    def supplier_address(self, siret: str) -> Address | None:
        """Address of the establishment of this SIRET, None if unknown or unusable."""

    def association_address(self, rna: str) -> Address | None:
        """Address of the head office of the association with this RNA number, None if
        unknown or unusable."""


def _street(establishment: dict, postal_code: str, city: str) -> str:
    """Street of an establishment.

    The head office (`siege`) has its street number, type and name; the address complement
    is left out, it often holds the name of a person. The `matching_etablissements` only
    have the whole `adresse` ("40 RUE DES CHANTIERS 76600 LE HAVRE"): the street is what
    comes before the postal code and the city.
    """
    if establishment.get("libelle_voie"):
        parts = ("numero_voie", "indice_repetition", "type_voie", "libelle_voie")
        return " ".join(establishment[part] for part in parts if establishment.get(part))
    whole = establishment.get("adresse") or ""
    suffix = f" {postal_code} {city}"
    return whole.removesuffix(suffix).strip() if whole.endswith(suffix) else ""


def _address(establishment: dict) -> Address | None:
    """`Address` of an establishment of the API; None if incomplete or not public."""
    postal_code = establishment.get("code_postal") or ""
    city = establishment.get("libelle_commune") or ""
    try:
        # Not public ("[ND]", "[NON-DIFFUSIBLE]") or missing values fail the validation.
        return Address(
            street=_street(establishment, postal_code, city), postal_code=postal_code, city=city
        )
    except ValidationError:
        return None


class RechercheEntreprisesRegistry:
    def __init__(self, base_url: str, timeout: float = 5) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _search(self, query: str) -> list[dict]:
        url = f"{self.base_url}/search?" + urllib.parse.urlencode({"q": query})
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                results = json.load(response)["results"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            # OSError covers URLError, HTTPError (429 included) and timeouts.
            raise RegistryUnavailable(str(exc)) from exc
        if not isinstance(results, list):
            raise RegistryUnavailable("unexpected answer")
        return results

    def supplier_address(self, siret: str) -> Address | None:
        """A 14-digit search is a direct SIRET search: the establishment of this SIRET is
        in the `matching_etablissements` of its legal unit."""
        try:
            for result in self._search(siret):
                for establishment in result["matching_etablissements"]:
                    if establishment["siret"] == siret:
                        return _address(establishment)
        except (KeyError, TypeError) as exc:
            raise RegistryUnavailable("unexpected answer") from exc
        return None

    def association_address(self, rna: str) -> Address | None:
        """A text search on the RNA number: only a result with this RNA number counts."""
        try:
            for result in self._search(rna):
                if (result["complements"] or {}).get("identifiant_association") == rna:
                    return _address(result["siege"])
        except (KeyError, TypeError, AttributeError) as exc:
            raise RegistryUnavailable("unexpected answer") from exc
        return None


def get_company_registry() -> CompanyRegistry:
    """FastAPI dependency: the registry of the settings (replaced in the tests)."""
    settings = get_settings()
    return RechercheEntreprisesRegistry(
        settings.company_registry_url, settings.company_registry_timeout_seconds
    )
