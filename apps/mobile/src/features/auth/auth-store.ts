import * as SecureStore from "expo-secure-store";
import { useEffect, useState } from "react";
import { Platform } from "react-native";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { AuthTokens, Me } from "./auth-api";

type AuthState = {
	tokens: AuthTokens | null;
	// Logged-in user, loaded from `GET /me`; not persisted, so it is fresh on each launch.
	me: Me | null;
	setTokens: (tokens: AuthTokens) => void;
	setMe: (me: Me) => void;
	clearTokens: () => void;
};

// Tokens go to the Keychain / Keystore; SecureStore has no web build, so Expo web falls back to localStorage.
const storage =
	Platform.OS === "web"
		? createJSONStorage(() => localStorage)
		: createJSONStorage(() => ({
				getItem: SecureStore.getItemAsync,
				setItem: SecureStore.setItemAsync,
				removeItem: SecureStore.deleteItemAsync,
			}));

/** Tokens of the logged-in user, persisted so the session survives an app restart. */
export const useAuthStore = create<AuthState>()(
	persist(
		(set) => ({
			tokens: null,
			me: null,
			setTokens: (tokens) => set({ tokens }),
			setMe: (me) => set({ me }),
			clearTokens: () => set({ tokens: null, me: null }),
		}),
		{
			// SecureStore keys only allow letters, digits, ".", "-" and "_".
			name: "gaspirator-auth",
			storage,
			partialize: (state) => ({ tokens: state.tokens }),
		},
	),
);

/** False until the saved tokens are read back: SecureStore is async, so the first render has none. */
export function useAuthHydrated(): boolean {
	// Starts false everywhere so Expo web's server render (no storage, no `persist`) matches the client.
	const [hydrated, setHydrated] = useState(false);
	useEffect(() => {
		const persist = useAuthStore.persist;
		if (!persist) return;
		if (persist.hasHydrated()) setHydrated(true);
		return persist.onFinishHydration(() => setHydrated(true));
	}, []);
	return hydrated;
}
