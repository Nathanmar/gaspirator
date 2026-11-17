"""Helpers shared by the Reservations tests."""

from tests.lots.helpers import assert_supplier_summary, parse

# `Reservation` of the contract; `pickup_code` is only sent to the association that reserved.
RESERVATION_FIELDS = {
    "id",
    "lot",
    "association",
    "quantity",
    "pickup_at",
    "status",
    "created_at",
    "collected_at",
}


def reservations_path(lot_id) -> str:
    return f"/lots/{lot_id}/reservations"


def reservation_path(reservation_id) -> str:
    return f"/reservations/{reservation_id}"


def assert_lot_summary(data: dict, lot) -> None:
    """`data` is the `LotSummary` of this `models.Lot`."""
    assert set(data) == {
        "id",
        "title",
        "unit",
        "divisible",
        "use_by_date",
        "storage",
        "pickup_start",
        "pickup_end",
        "supplier",
    }
    assert data["id"] == lot.id
    assert data["title"] == lot.title
    assert data["unit"] == lot.unit.value
    assert data["divisible"] is lot.divisible
    assert data["use_by_date"] == lot.use_by_date.isoformat()
    assert data["storage"] == lot.storage.value
    assert parse(data["pickup_start"]) == lot.pickup_start
    assert parse(data["pickup_end"]) == lot.pickup_end
    assert_supplier_summary(data["supplier"], lot.supplier)


def assert_association_summary(data: dict, association) -> None:
    """`data` is the `AssociationSummary` of this `models.Association`."""
    assert data == {
        "id": association.id,
        "name": association.name,
        "address": {
            "street": association.street,
            "postal_code": association.postal_code,
            "city": association.city,
        },
        "location": {"latitude": association.latitude, "longitude": association.longitude},
        "contact_phone": association.contact_phone,
    }
