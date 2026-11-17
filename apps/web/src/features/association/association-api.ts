import type {
	AssociationSummary,
	SupplierSummary,
} from "@/features/auth/auth-api";
import { authorizedRequest } from "@/features/auth/authorized-request";
import type { Page } from "@/lib/api-client";

export type QuantityUnit = "portions" | "kg" | "pieces";
export type Storage = "ambient" | "refrigerated" | "frozen";

export type SupplierSearchResult = SupplierSummary & {
	distance_km: number;
	available_lots_count: number;
};

export type LotSummary = {
	id: number;
	title: string;
	unit: QuantityUnit;
	divisible: boolean;
	use_by_date: string;
	storage: Storage;
	pickup_start: string;
	pickup_end: string;
	supplier: SupplierSummary;
};

export type Reservation = {
	id: number;
	lot: LotSummary;
	association: AssociationSummary;
	quantity: number;
	pickup_at: string;
	status: "booked" | "collected";
	// Only sent to the association that booked the lot.
	pickup_code?: string;
	created_at: string;
	collected_at: string | null;
};

/** `GET /suppliers`: suppliers with at least one available lot, nearest first. */
export function searchSuppliers({
	radius_km,
}: {
	radius_km: number;
}): Promise<Page<SupplierSearchResult>> {
	const query = new URLSearchParams({ radius_km: String(radius_km) });
	return authorizedRequest(`/suppliers?${query}`, { method: "GET" });
}

/** `GET /me/reservations`: most recently booked first, with their pickup codes. */
export function listMyReservations({
	per_page,
}: {
	per_page?: number;
} = {}): Promise<Page<Reservation>> {
	const query = per_page
		? `?${new URLSearchParams({ per_page: String(per_page) })}`
		: "";
	return authorizedRequest(`/me/reservations${query}`, { method: "GET" });
}

/** `GET /reservations/{id}`: the association that booked it also gets the pickup code. */
export function getReservation(id: number): Promise<Reservation> {
	return authorizedRequest(`/reservations/${id}`, { method: "GET" });
}
