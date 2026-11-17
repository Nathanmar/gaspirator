"""Helpers shared by the Suppliers tests."""

from math import asin, cos, radians, sin, sqrt

SUPPLIER_SUMMARY_FIELDS = {
    "id",
    "name",
    "supplier_type",
    "address",
    "location",
    "contact_phone",
}


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Reference great-circle distance, to check the SQL computation."""
    (lat1, lon1), (lat2, lon2) = a, b
    h = (
        sin(radians(lat2 - lat1) / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(radians(lon2 - lon1) / 2) ** 2
    )
    return 2 * 6371 * asin(sqrt(h))
