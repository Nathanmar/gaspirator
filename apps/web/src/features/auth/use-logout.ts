import { useRef } from "react";

import { toast } from "sonner";

import { ApiError, NetworkError } from "@/lib/api-client";

import { logout } from "./auth-api";
import { useAuthStore } from "./auth-store";

/**
 * Ends the session: revokes the refresh token on the API, then forgets the tokens. The local
 * session ends even when the API call fails (expired access token, server down): the user asked
 * to leave, and the revocation on the server is a best effort.
 */
export function useLogout() {
	const tokens = useAuthStore((state) => state.tokens);
	const clearTokens = useAuthStore((state) => state.clearTokens);
	// A ref, not a state: a second tap can come before React re-renders.
	const isLoggingOut = useRef(false);

	return async function logOut() {
		if (isLoggingOut.current) return;
		isLoggingOut.current = true;
		try {
			if (tokens) {
				try {
					await logout(tokens);
				} catch (error) {
					// Anything else than an API or network failure is a bug: let it surface.
					if (!(error instanceof ApiError || error instanceof NetworkError))
						throw error;
				}
			}
			clearTokens();
			toast.success("Vous êtes déconnecté.");
		} finally {
			isLoggingOut.current = false;
		}
	};
}
