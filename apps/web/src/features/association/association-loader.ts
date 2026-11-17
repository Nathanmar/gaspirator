import { redirect } from "@tanstack/react-router";
import { toast } from "sonner";
import { z } from "zod";

import type { Association } from "@/features/auth/auth-api";
import { SessionExpiredError } from "@/features/auth/authorized-request";
import { getMe } from "@/features/auth/me";
import type { Page } from "@/lib/api-client";

import {
	getReservation,
	listMyReservations,
	type Reservation,
	type SupplierSearchResult,
	searchSuppliers,
} from "./association-api";

export const RADIUS_OPTIONS = [5, 10, 25, 50] as const;
export const DEFAULT_RADIUS_KM = 10;

export const associationSearchSchema = z.object({
	radius_km: z.literal(RADIUS_OPTIONS).optional().catch(undefined),
});

export type AssociationAccount = {
	firstname: string;
	association: Association;
};

export type AssociationHomeData = AssociationAccount & {
	reservations: Reservation[];
	suppliers: Page<SupplierSearchResult>;
};

async function withSession<T>(load: () => Promise<T>): Promise<T> {
	try {
		return await load();
	} catch (error) {
		if (error instanceof SessionExpiredError) {
			// The id keeps a single message when several loaders find the session expired at once.
			toast.info(error.message, { id: "session-expired" });
			throw redirect({ to: "/login", search: { role: "association" } });
		}
		throw error;
	}
}

export function loadAssociationAccount(): Promise<AssociationAccount> {
	return withSession(async () => {
		const me = await getMe();
		if (!me.association) throw redirect({ to: "/" });
		return { firstname: me.firstname, association: me.association };
	});
}

export function loadAssociationHome(radius: number) {
	return withSession(async () => {
		const [reservations, suppliers] = await Promise.all([
			listMyReservations(),
			searchSuppliers({ radius_km: radius }),
		]);
		return { reservations: reservations.data, suppliers };
	});
}

export function loadReservationHistory(): Promise<Reservation[]> {
	return withSession(
		async () => (await listMyReservations({ per_page: 100 })).data,
	);
}

export function loadReservation(id: number): Promise<Reservation> {
	return withSession(() => getReservation(id));
}
