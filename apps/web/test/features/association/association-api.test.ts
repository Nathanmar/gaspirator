import { beforeEach, describe, expect, it } from "vitest";

import {
	listMyReservations,
	searchSuppliers,
} from "@/features/association/association-api";
import { useAuthStore } from "@/features/auth/auth-store";

import {
	firstPage,
	nearbySupplier,
	soonReservation,
} from "../../fixtures/association";
import { tokens } from "../../fixtures/auth";
import { jsonResponse, mockFetch, requestedPaths } from "../../utils/fetch";

beforeEach(() => {
	useAuthStore.setState({ tokens });
});

describe("searchSuppliers", () => {
	it("searches around the association within the given radius", async () => {
		const page = firstPage([nearbySupplier]);
		const fetchMock = mockFetch(jsonResponse(200, page));

		await expect(searchSuppliers({ radius_km: 25 })).resolves.toEqual(page);
		expect(requestedPaths(fetchMock)).toEqual(["/suppliers?radius_km=25"]);
		expect(
			new Headers(fetchMock.mock.calls[0][1]?.headers).get("Authorization"),
		).toBe("Bearer access");
	});
});

describe("listMyReservations", () => {
	it("lists the reservations of the association", async () => {
		const page = firstPage([soonReservation]);
		const fetchMock = mockFetch(jsonResponse(200, page));

		await expect(listMyReservations()).resolves.toEqual(page);
		expect(requestedPaths(fetchMock)).toEqual(["/me/reservations"]);
	});
});
