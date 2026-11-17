import { ApiError, apiRequest } from "@/lib/api-client";

import { type AuthTokens, refreshTokens } from "./auth-api";
import { useAuthStore } from "./auth-store";

/** There is no session left to use: the user has to log in again. */
export class SessionExpiredError extends Error {
	constructor() {
		super("Votre session a expiré. Reconnectez-vous.");
		this.name = "SessionExpiredError";
	}
}

type AuthorizedRequestOptions = {
	method: "GET" | "POST";
	body?: unknown;
};

/**
 * Calls a route reserved to logged-in users. When the access token has expired (401), the tokens
 * are renewed once and the request is sent again.
 *
 * @throws {SessionExpiredError} when there is no session or it cannot be renewed.
 */
export async function authorizedRequest<T>(
	path: string,
	options: AuthorizedRequestOptions,
): Promise<T> {
	const tokens = useAuthStore.getState().tokens;
	if (!tokens) throw new SessionExpiredError();

	try {
		return await apiRequest<T>(path, {
			...options,
			accessToken: tokens.access_token,
		});
	} catch (error) {
		if (!(error instanceof ApiError && error.status === 401)) throw error;
	}

	const renewed = await renewTokens(tokens);
	return apiRequest<T>(path, { ...options, accessToken: renewed.access_token });
}

// Shared by the requests that find the token expired at the same time: the API invalidates a
// refresh token once used, so a second renewal with the same one would end the session.
let pendingRenewal: Promise<AuthTokens> | null = null;

function renewTokens(expired: AuthTokens): Promise<AuthTokens> {
	const current = useAuthStore.getState().tokens;
	if (current && current.access_token !== expired.access_token) {
		return Promise.resolve(current);
	}
	pendingRenewal ??= renewSession(expired.refresh_token).finally(() => {
		pendingRenewal = null;
	});
	return pendingRenewal;
}

async function renewSession(refreshToken: string): Promise<AuthTokens> {
	const { setTokens, clearTokens } = useAuthStore.getState();
	try {
		const tokens = await refreshTokens(refreshToken);
		setTokens(tokens);
		return tokens;
	} catch (error) {
		// A refused refresh token ends the session; a server error or no network does not.
		if (error instanceof ApiError && error.status < 500) {
			clearTokens();
			throw new SessionExpiredError();
		}
		throw error;
	}
}
