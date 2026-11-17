import { isRedirect } from "@tanstack/react-router";
import { beforeEach, describe, expect, it } from "vitest";

import { redirectIfLoggedIn } from "@/features/auth/auth-guard";
import { useAuthStore } from "@/features/auth/auth-store";

import { tokens } from "../../fixtures/auth";

beforeEach(() => {
	useAuthStore.setState({ tokens: null });
});

describe("redirectIfLoggedIn", () => {
	it("lets a visitor open the login and registration pages", () => {
		expect(() => redirectIfLoggedIn()).not.toThrow();
	});

	it("sends a logged-in user to the home page", () => {
		useAuthStore.setState({ tokens });

		const thrown = (() => {
			try {
				redirectIfLoggedIn();
			} catch (error) {
				return error;
			}
		})();

		expect(isRedirect(thrown)).toBe(true);
		expect(thrown).toMatchObject({ options: { to: "/" } });
	});
});
