import type { QuantityUnit } from "@/features/association/association-api";
import type { Address } from "@/features/auth/auth-api";

// Everyone reads pickup times in Lyon time, so the supplier and the association agree on the hour
// even if a device is set to another time zone.
const TIME_ZONE = "Europe/Paris";

const NBSP = " ";

const distance = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 });
const quantity = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 });
const day = new Intl.DateTimeFormat("fr-FR", {
	weekday: "short",
	day: "numeric",
	month: "short",
	timeZone: TIME_ZONE,
});
const time = new Intl.DateTimeFormat("fr-FR", {
	hour: "2-digit",
	minute: "2-digit",
	timeZone: TIME_ZONE,
});

const UNITS: Record<QuantityUnit, { one: string; many: string }> = {
	portions: { one: "portion", many: "portions" },
	kg: { one: "kg", many: "kg" },
	pieces: { one: "pièce", many: "pièces" },
};

export function formatDistance(km: number): string {
	if (km < 1) return `${Math.round(km * 1000)}${NBSP}m`;
	return `${distance.format(km)}${NBSP}km`;
}

export function formatQuantity(amount: number, unit: QuantityUnit): string {
	// In French, the singular goes up to 2 excluded ("1,5 portion").
	const label = amount < 2 ? UNITS[unit].one : UNITS[unit].many;
	return `${quantity.format(amount)}${NBSP}${label}`;
}

export function formatDateTime(iso: string): string {
	const date = new Date(iso);
	return `${day.format(date)} à ${time.format(date)}`;
}

export function formatPickupWindow(startIso: string, endIso: string): string {
	const start = new Date(startIso);
	const end = new Date(endIso);
	if (start.getTime() === end.getTime()) return formatDateTime(startIso);
	if (day.format(start) === day.format(end)) {
		return `${day.format(start)}, entre ${time.format(start)} et ${time.format(end)}`;
	}
	return `du ${formatDateTime(startIso)} au ${formatDateTime(endIso)}`;
}

const month = new Intl.DateTimeFormat("fr-FR", {
	month: "long",
	year: "numeric",
	timeZone: TIME_ZONE,
});

export function formatMonth(iso: string): string {
	const label = month.format(new Date(iso));
	return label.charAt(0).toUpperCase() + label.slice(1);
}

export function pluralize(count: number, one: string, many: string): string {
	return `${count} ${count > 1 ? many : one}`;
}

// A calendar date (use-by date) has no time: read in UTC, it never moves to the day before.
const calendarDay = new Intl.DateTimeFormat("fr-FR", {
	weekday: "short",
	day: "numeric",
	month: "short",
	timeZone: "UTC",
});

export function formatDate(isoDate: string): string {
	return calendarDay.format(new Date(`${isoDate}T00:00:00Z`));
}

export function formatPickupCode(code: string): string {
	return `${code.slice(0, 3)}${NBSP}${code.slice(3)}`;
}

export function formatAddress({ street, postal_code, city }: Address): string {
	return `${street}, ${postal_code} ${city}`;
}
