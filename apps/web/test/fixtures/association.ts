import type {
	Reservation,
	SupplierSearchResult,
} from "@/features/association/association-api";
import type { Me, SupplierSummary } from "@/features/auth/auth-api";

const association = {
	id: 7,
	name: "Restos du Cœur Lyon 2",
	address: {
		street: "12 rue de la République",
		postal_code: "69002",
		city: "Lyon",
	},
	location: { latitude: 45.7578, longitude: 4.832 },
	contact_phone: "04 78 00 00 01",
} as const;

export const associationMe = {
	id: 5,
	email: "marie.dupont@example.org",
	firstname: "Marie",
	lastname: "Dupont",
	role: "manager",
	supplier: null,
	association: {
		...association,
		legal_id: "W691234567",
		created_at: "2026-11-01T09:00:00Z",
	},
} as const satisfies Me;

const canteen = {
	id: 3,
	name: "Cantine du lycée Ampère",
	supplier_type: "canteen",
	address: {
		street: "31 rue de la Bourse",
		postal_code: "69002",
		city: "Lyon",
	},
	location: { latitude: 45.7631, longitude: 4.8357 },
	contact_phone: "04 78 00 00 00",
} as const satisfies SupplierSummary;

const hospital = {
	id: 4,
	name: "Hôpital Édouard-Herriot",
	supplier_type: "hospital",
	address: {
		street: "5 place d'Arsonval",
		postal_code: "69003",
		city: "Lyon",
	},
	location: { latitude: 45.7454, longitude: 4.8818 },
	contact_phone: "04 72 11 73 11",
} as const satisfies SupplierSummary;

export const supplierMe = {
	...associationMe,
	association: null,
	supplier: {
		...canteen,
		legal_id: "19690103400017",
		created_at: "2026-11-01T09:00:00Z",
	},
} as const satisfies Me;

export const adminMe = {
	...associationMe,
	role: "admin",
	association: null,
} as const satisfies Me;

export const nearbySupplier = {
	...canteen,
	distance_km: 0.35,
	available_lots_count: 2,
} as const satisfies SupplierSearchResult;

export const fartherSupplier = {
	...hospital,
	distance_km: 4.267,
	available_lots_count: 1,
} as const satisfies SupplierSearchResult;

const parmentier = {
	id: 41,
	title: "Hachis parmentier",
	unit: "portions",
	divisible: true,
	use_by_date: "2026-11-04",
	storage: "refrigerated",
	pickup_start: "2026-11-03T13:00:00Z",
	pickup_end: "2026-11-03T15:00:00Z",
	supplier: canteen,
} as const;

// Times are in UTC: 14:15Z is 15:15 in Lyon in November.
export const soonReservation = {
	id: 3,
	lot: parmentier,
	association,
	quantity: 12,
	pickup_at: "2026-11-03T14:15:00Z",
	status: "booked",
	pickup_code: "482913",
	created_at: "2026-11-02T10:00:00Z",
	collected_at: null,
} as const satisfies Reservation;

export const laterReservation = {
	id: 4,
	lot: {
		...parmentier,
		id: 42,
		title: "Yaourts nature",
		unit: "pieces",
		pickup_start: "2026-11-05T08:00:00Z",
		pickup_end: "2026-11-05T10:00:00Z",
		supplier: hospital,
	},
	association,
	quantity: 24,
	pickup_at: "2026-11-05T09:30:00Z",
	status: "booked",
	pickup_code: "105377",
	created_at: "2026-11-02T11:00:00Z",
	collected_at: null,
} as const satisfies Reservation;

export const collectedReservation = {
	id: 2,
	lot: {
		...parmentier,
		id: 40,
		title: "Pain de campagne",
		unit: "kg",
		storage: "ambient",
	},
	association,
	quantity: 3.5,
	pickup_at: "2026-11-01T17:00:00Z",
	status: "collected",
	pickup_code: "730114",
	created_at: "2026-10-31T08:00:00Z",
	collected_at: "2026-11-01T17:05:00Z",
} as const satisfies Reservation;

/** First page of a paginated list (`{ data, meta }` in the contract). */
export function firstPage<T>(data: T[]) {
	return { data, meta: { page: 1, per_page: 20, total: data.length } };
}
