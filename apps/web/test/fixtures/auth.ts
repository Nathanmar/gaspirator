import type { AuthTokens } from "@/features/auth/auth-api";

// Tokens returned by `POST /auth/login`.
export const tokens: AuthTokens = {
	access_token: "access",
	refresh_token: "refresh",
	token_type: "Bearer",
	expires_in: 900,
};
