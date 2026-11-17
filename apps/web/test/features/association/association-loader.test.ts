import { isRedirect } from "@tanstack/react-router";
import { toast } from "sonner";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
	associationSearchSchema,
	loadAssociationHome,
} from "@/features/association/association-loader";
import { useAuthStore } from "@/features/auth/auth-store";

import {
	associationMe,
	firstPage,
	nearbySupplier,
	soonReservation,
	supplierMe,
} from "../../fixtures/association";
import { tokens } from "../../fixtures/auth";
import { jsonResponse, mockApi, requestedPaths } from "../../utils/fetch";

beforeEach(() => {
	useAuthStore.setState({ tokens });
});

describe("loadAssociationHome", () => {
	it("loads the manager, the reservations and the suppliers around", async () => {
		const fetchMock = mockApi({
			"/me": jsonResponse(200, associationMe),
			"/me/reservations": jsonResponse(200, firstPage([soonReservation])),
			"/suppliers": jsonResponse(200, firstPage([nearbySupplier])),
		});

		await expect(loadAssociationHome(25)).resolves.toEqual({
			firstname: "Marie",
			association: associationMe.association,
			reservations: [soonReservation],
			suppliers: firstPage([nearbySupplier]),
		});
		expect(requestedPaths(fetchMock)).toContain("/suppliers?radius_km=25");
	});

	it("sends an account that runs no association to the home page", async () => {
		const fetchMock = mockApi({ "/me": jsonResponse(200, supplierMe) });

		const thrown = await loadAssociationHome(10).catch((error) => error);

		expect(isRedirect(thrown)).toBe(true);
		expect(thrown).toMatchObject({ options: { to: "/" } });
		expect(requestedPaths(fetchMock)).toEqual(["/me"]);
	});

	it("sends back to the login page once the session has expired", async () => {
		const info = vi.spyOn(toast, "info");
		const expired = jsonResponse(401, {
			code: "unauthorized",
			message: "Token invalide ou expiré.",
		});
		mockApi({ "/me": expired, "/auth/refresh": expired });

		const thrown = await loadAssociationHome(10).catch((error) => error);

		expect(isRedirect(thrown)).toBe(true);
		expect(thrown).toMatchObject({
			options: { to: "/login", search: { role: "association" } },
		});
		expect(info).toHaveBeenCalledWith(
			"Votre session a expiré. Reconnectez-vous.",
		);
	});
});

describe("associationSearchSchema", () => {
	it("keeps a search radius offered by the page", () => {
		expect(associationSearchSchema.parse({ radius_km: 25 })).toEqual({
			radius_km: 25,
		});
	});

	it("drops any other radius instead of breaking the page", () => {
		expect(associationSearchSchema.parse({ radius_km: 7 })).toEqual({});
		expect(associationSearchSchema.parse({ radius_km: "loin" })).toEqual({});
	});
});
