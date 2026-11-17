"""Geocoding of the registration addresses (US-01) with the Géoplateforme of the IGN.

API: https://data.geopf.fr/geocodage (free, no key), built on the Base Adresse Nationale.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Protocol

from app.schemas import Address, GeoPoint
from app.settings import get_settings

# Below this score, the best match is another street nearby rather than this address
# (≈ 0.97 for an exact address, ≈ 0.4 for a street that does not exist).
MIN_SCORE = 0.6


class GeocodingUnavailable(Exception):
    """The geocoding service could not be reached or gave an unexpected answer."""


class Geocoder(Protocol):
    def geocode(self, address: Address) -> GeoPoint | None:
        """Position of the address, None if it cannot be found."""


class GeoplateformeGeocoder:
    def __init__(self, base_url: str, timeout: float = 5) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def geocode(self, address: Address) -> GeoPoint | None:
        """Best match of the address within its postal code, if its score is high enough.

        Raises `GeocodingUnavailable` if the service fails.
        """
        query = urllib.parse.urlencode(
            {
                "q": f"{address.street} {address.city}",
                "index": "address",
                "postcode": address.postal_code,
                "limit": 1,
            }
        )
        try:
            with urllib.request.urlopen(
                f"{self.base_url}/search?{query}", timeout=self.timeout
            ) as response:
                features = json.load(response)["features"]
            if not features:
                return None
            best = features[0]
            if best["properties"]["score"] < MIN_SCORE:
                return None
            longitude, latitude = best["geometry"]["coordinates"][:2]
            return GeoPoint(latitude=latitude, longitude=longitude)
        except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            # OSError covers URLError, HTTPError and timeouts; ValueError covers bad JSON.
            raise GeocodingUnavailable(str(exc)) from exc


def get_geocoder() -> Geocoder:
    """FastAPI dependency: the geocoder of the settings (replaced in the tests)."""
    settings = get_settings()
    return GeoplateformeGeocoder(settings.geocoding_url, settings.geocoding_timeout_seconds)
