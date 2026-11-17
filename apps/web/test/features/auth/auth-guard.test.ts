import { isRedirect } from "@tanstack/react-router";
import { beforeEach, describe, expect, it } from "vitest";

import { redirectIfLoggedIn, requireLogin } from "@/features/auth/auth-guard";
import { useAuthStore } from "@/features/auth/auth-store";

import { tokens } from "../../fixtures/auth";

beforeEach(() => {
	useAuthStore.setState({ tokens: null });
});

function thrownBy(guard: () => void) {
	try {
		guard();
	} catch (error) {
		return error;
	}
}

describe("requireLogin", () => {
	it("lets a logged-in user open the page", () => {
		useAuthStore.setState({ tokens });

		expect(() => requireLogin("association")).not.toThrow();
	});

	it("sends a visitor to the login page of the space", () => {
		const thrown = thrownBy(() => requireLogin("association"));

		expect(isRedirect(thrown)).toBe(true);
		expect(thrown).toMatchObject({
			options: { to: "/login", search: { role: "association" } },
		});
	});
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
