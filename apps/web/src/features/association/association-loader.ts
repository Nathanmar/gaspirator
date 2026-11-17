import { redirect } from "@tanstack/react-router";
import { toast } from "sonner";
import { z } from "zod";

import type { Association } from "@/features/auth/auth-api";
import { SessionExpiredError } from "@/features/auth/authorized-request";
import { getMe } from "@/features/auth/me";
import type { Page } from "@/lib/api-client";

import {
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

export type AssociationHomeData = {
	firstname: string;
	association: Association;
	reservations: Reservation[];
	suppliers: Page<SupplierSearchResult>;
};

export async function loadAssociationHome(
	radius: number,
): Promise<AssociationHomeData> {
	try {
		const me = await getMe();
		if (!me.association) throw redirect({ to: "/" });

		const [reservations, suppliers] = await Promise.all([
			listMyReservations(),
			searchSuppliers({ radius_km: radius }),
		]);
		return {
			firstname: me.firstname,
			association: me.association,
			reservations: reservations.data,
			suppliers,
		};
	} catch (error) {
		if (error instanceof SessionExpiredError) {
			toast.info(error.message);
			throw redirect({ to: "/login", search: { role: "association" } });
		}
		throw error;
	}
}
