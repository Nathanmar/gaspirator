import { beforeEach, describe, expect, it } from "vitest";

import { useAuthStore } from "@/features/auth/auth-store";
import { getMe, homePath } from "@/features/auth/me";

import { adminMe, associationMe, supplierMe } from "../../fixtures/association";
import { tokens } from "../../fixtures/auth";
import { jsonResponse, mockFetch, requestedPaths } from "../../utils/fetch";

beforeEach(() => {
	useAuthStore.setState({ tokens });
});

describe("getMe", () => {
	it("asks the API who is logged in", async () => {
		const fetchMock = mockFetch(jsonResponse(200, associationMe));

		await expect(getMe()).resolves.toEqual(associationMe);
		expect(requestedPaths(fetchMock)).toEqual(["/me"]);
		expect(fetchMock.mock.calls[0][1]?.method).toBe("GET");
	});
});

describe("homePath", () => {
	it("sends the manager of an association to the association space", () => {
		expect(homePath(associationMe)).toBe("/association");
	});

	it("sends every other account to the home page for now", () => {
		expect(homePath(supplierMe)).toBe("/");
		expect(homePath(adminMe)).toBe("/");
	});
});
