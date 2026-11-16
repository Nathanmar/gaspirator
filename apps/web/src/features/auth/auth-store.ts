import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { AuthTokens } from "./auth-api";

type AuthState = {
  tokens: AuthTokens | null;
  setTokens: (tokens: AuthTokens) => void;
  clearTokens: () => void;
};

/**
 * Tokens of the logged-in user, kept in localStorage so the session survives a page reload.
 * The contract returns the tokens in the response body, so they cannot live in an httpOnly cookie.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      tokens: null,
      setTokens: (tokens) => set({ tokens }),
      clearTokens: () => set({ tokens: null }),
    }),
    {
      name: "gaspirator-auth",
      // Only the data is saved, not the actions.
      partialize: (state) => ({ tokens: state.tokens }),
    },
  ),
);
