import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "@/features/auth/auth-store";
import {
	authorizedRequest,
	SessionExpiredError,
} from "@/features/auth/authorized-request";
import { NetworkError } from "@/lib/api-client";

import { tokens } from "../../fixtures/auth";
import { jsonResponse, mockFetch, requestedPaths } from "../../utils/fetch";

const renewed = {
	...tokens,
	access_token: "new-access",
	refresh_token: "new-refresh",
};

function expired() {
	return jsonResponse(401, {
		code: "unauthorized",
		message: "Token invalide ou expiré.",
	});
}

function authorization(
	fetchMock: ReturnType<typeof vi.fn<typeof fetch>>,
	call: number,
) {
	return new Headers(fetchMock.mock.calls[call][1]?.headers).get(
		"Authorization",
	);
}

function mockSequence(...responses: Array<Response | Error>) {
	const fetchMock = vi.fn<typeof fetch>();
	for (const response of responses) {
		if (response instanceof Error) fetchMock.mockRejectedValueOnce(response);
		else fetchMock.mockResolvedValueOnce(response);
	}
	globalThis.fetch = fetchMock;
	return fetchMock;
}

beforeEach(() => {
	useAuthStore.setState({ tokens });
});

describe("authorizedRequest", () => {
	it("sends the access token of the session", async () => {
		const fetchMock = mockFetch(jsonResponse(200, { ok: true }));

		await expect(authorizedRequest("/me", { method: "GET" })).resolves.toEqual({
			ok: true,
		});
		expect(requestedPaths(fetchMock)).toEqual(["/me"]);
		expect(authorization(fetchMock, 0)).toBe("Bearer access");
	});

	it("renews the tokens once the access token has expired, then retries", async () => {
		const fetchMock = mockSequence(
			expired(),
			jsonResponse(200, renewed),
			jsonResponse(200, { ok: true }),
		);

		await expect(authorizedRequest("/me", { method: "GET" })).resolves.toEqual({
			ok: true,
		});
		expect(requestedPaths(fetchMock)).toEqual(["/me", "/auth/refresh", "/me"]);
		expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toEqual({
			refresh_token: "refresh",
		});
		expect(authorization(fetchMock, 2)).toBe("Bearer new-access");
		expect(useAuthStore.getState().tokens).toEqual(renewed);
	});

	it("renews the tokens only once for requests that expire together", async () => {
		// The API replaces the refresh token on each use: a second refresh with the old one fails.
		const fetchMock = vi.fn<typeof fetch>(async (input, init) => {
			if (String(input).endsWith("/auth/refresh"))
				return jsonResponse(200, renewed);
			const isRenewed =
				new Headers(init?.headers).get("Authorization") === "Bearer new-access";
			return isRenewed ? jsonResponse(200, { ok: true }) : expired();
		});
		globalThis.fetch = fetchMock;

		await Promise.all([
			authorizedRequest("/me", { method: "GET" }),
			authorizedRequest("/me/reservations", { method: "GET" }),
		]);

		expect(
			requestedPaths(fetchMock).filter((path) => path === "/auth/refresh"),
		).toHaveLength(1);
	});

	it("ends the session when the refresh token is refused too", async () => {
		mockSequence(expired(), expired());

		await expect(
			authorizedRequest("/me", { method: "GET" }),
		).rejects.toBeInstanceOf(SessionExpiredError);
		expect(useAuthStore.getState().tokens).toBeNull();
	});

	it("keeps the session when the server cannot be reached to renew it", async () => {
		mockSequence(expired(), new TypeError("Failed to fetch"));

		await expect(
			authorizedRequest("/me", { method: "GET" }),
		).rejects.toBeInstanceOf(NetworkError);
		expect(useAuthStore.getState().tokens).toEqual(tokens);
	});

	it("does not call the API without a session", async () => {
		useAuthStore.setState({ tokens: null });
		const fetchMock = mockFetch(jsonResponse(200, {}));

		await expect(
			authorizedRequest("/me", { method: "GET" }),
		).rejects.toBeInstanceOf(SessionExpiredError);
		expect(fetchMock).not.toHaveBeenCalled();
	});
});
