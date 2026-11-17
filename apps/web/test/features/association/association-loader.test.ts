import { isRedirect } from "@tanstack/react-router";
import { toast } from "sonner";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
	associationSearchSchema,
	loadAssociationAccount,
	loadAssociationHome,
	loadReservation,
	loadReservationHistory,
} from "@/features/association/association-loader";
import { useAuthStore } from "@/features/auth/auth-store";

import {
	associationMe,
	collectedReservation,
	firstPage,
	nearbySupplier,
	soonReservation,
	supplierMe,
} from "../../fixtures/association";
import { tokens } from "../../fixtures/auth";
import { jsonResponse, mockApi, requestedPaths } from "../../utils/fetch";

const expired = jsonResponse(401, {
	code: "unauthorized",
	message: "Token invalide ou expiré.",
});

beforeEach(() => {
	useAuthStore.setState({ tokens });
});

describe("loadAssociationAccount", () => {
	it("loads the manager and the association", async () => {
		mockApi({ "/me": jsonResponse(200, associationMe) });

		await expect(loadAssociationAccount()).resolves.toEqual({
			firstname: "Marie",
			association: associationMe.association,
		});
	});

	it("sends an account that runs no association to the home page", async () => {
		mockApi({ "/me": jsonResponse(200, supplierMe) });

		const thrown = await loadAssociationAccount().catch((error) => error);

		expect(isRedirect(thrown)).toBe(true);
		expect(thrown).toMatchObject({ options: { to: "/" } });
	});

	it("sends back to the login page once the session has expired", async () => {
		const info = vi.spyOn(toast, "info");
		mockApi({ "/me": expired, "/auth/refresh": expired });

		const thrown = await loadAssociationAccount().catch((error) => error);

		expect(isRedirect(thrown)).toBe(true);
		expect(thrown).toMatchObject({
			options: { to: "/login", search: { role: "association" } },
		});
		expect(info).toHaveBeenCalledWith(
			"Votre session a expiré. Reconnectez-vous.",
			expect.anything(),
		);
	});
});

describe("loadAssociationHome", () => {
	it("loads the reservations and the suppliers around", async () => {
		const fetchMock = mockApi({
			"/me/reservations": jsonResponse(200, firstPage([soonReservation])),
			"/suppliers": jsonResponse(200, firstPage([nearbySupplier])),
		});

		await expect(loadAssociationHome(25)).resolves.toEqual({
			reservations: [soonReservation],
			suppliers: firstPage([nearbySupplier]),
		});
		expect(requestedPaths(fetchMock)).toContain("/suppliers?radius_km=25");
	});

	it("sends back to the login page once the session has expired", async () => {
		mockApi({
			"/me/reservations": expired,
			"/suppliers": expired,
			"/auth/refresh": expired,
		});

		const thrown = await loadAssociationHome(10).catch((error) => error);

		expect(thrown).toMatchObject({ options: { to: "/login" } });
	});
});

describe("loadReservationHistory", () => {
	it("loads up to 100 reservations, the most a page holds", async () => {
		const fetchMock = mockApi({
			"/me/reservations": jsonResponse(200, firstPage([collectedReservation])),
		});

		await expect(loadReservationHistory()).resolves.toEqual([
			collectedReservation,
		]);
		expect(requestedPaths(fetchMock)).toEqual([
			"/me/reservations?per_page=100",
		]);
	});
});

describe("loadReservation", () => {
	it("loads one reservation", async () => {
		mockApi({ "/reservations/3": jsonResponse(200, soonReservation) });

		await expect(loadReservation(3)).resolves.toEqual(soonReservation);
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
