"""Helpers shared by the Lots tests."""

from datetime import UTC, date, datetime, time

LOT_FIELDS = {
    "id",
    "supplier",
    "title",
    "category",
    "quantity",
    "remaining_quantity",
    "unit",
    "divisible",
    "use_by_date",
    "allergens",
    "storage",
    "pickup_start",
    "pickup_end",
    "status",
    "created_at",
}


def today() -> date:
    """Today in UTC, the reference of the contract for the use-by date."""
    return datetime.now(UTC).date()


def at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=UTC)


def iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value)


def assert_error(response, status: int, code: str) -> dict:
    """The response is an `Error` with this status and code, and a message."""
    assert response.status_code == status
    data = response.json()
    assert data["code"] == code
    assert isinstance(data["message"], str) and data["message"]
    return data


def assert_supplier_summary(data: dict, supplier) -> None:
    """`data` is the `SupplierSummary` of this `models.Supplier`."""
    assert data == {
        "id": supplier.id,
        "name": supplier.name,
        "supplier_type": supplier.supplier_type.value,
        "address": {
            "street": supplier.street,
            "postal_code": supplier.postal_code,
            "city": supplier.city,
        },
        "location": {"latitude": supplier.latitude, "longitude": supplier.longitude},
        "contact_phone": supplier.contact_phone,
    }
