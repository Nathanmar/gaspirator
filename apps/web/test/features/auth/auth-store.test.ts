import { beforeEach, describe, expect, it } from "vitest";

import { useAuthStore } from "@/features/auth/auth-store";

import { tokens } from "../../fixtures/auth";

beforeEach(() => {
	useAuthStore.setState({ tokens: null });
});

describe("useAuthStore", () => {
	it("keeps the tokens in localStorage so the session survives a page reload", () => {
		useAuthStore.getState().setTokens(tokens);

		expect(useAuthStore.getState().tokens).toEqual(tokens);
		const saved = JSON.parse(localStorage.getItem("gaspirator-auth") ?? "{}");
		expect(saved.state.tokens).toEqual(tokens);
	});

	it("forgets the tokens on logout", () => {
		useAuthStore.getState().setTokens(tokens);

		useAuthStore.getState().clearTokens();

		expect(useAuthStore.getState().tokens).toBeNull();
	});
});
