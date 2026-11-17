import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { JoinButtons } from "@/components/landing/join-buttons";
import { useAuthStore } from "@/features/auth/auth-store";

import { tokens } from "../../fixtures/auth";
import { renderWithRouter } from "../../utils/render-with-router";

beforeEach(() => {
	useAuthStore.setState({ tokens: null });
});

describe("JoinButtons", () => {
	it("sends a visitor to the login page of each space", async () => {
		renderWithRouter(<JoinButtons />);

		expect(
			await screen.findByRole("link", { name: /Je suis fournisseur/ }),
		).toHaveAttribute("href", "/login?role=supplier");
		expect(
			screen.getByRole("link", { name: /Je suis une association/ }),
		).toHaveAttribute("href", "/login?role=association");
	});

	it("gives a logged-in user a single way into their space", async () => {
		useAuthStore.setState({ tokens });
		renderWithRouter(<JoinButtons />);

		expect(
			await screen.findByRole("link", { name: /Accéder à mon espace/ }),
		).toHaveAttribute("href", "/association");
		expect(
			screen.queryByRole("link", { name: /Je suis/ }),
		).not.toBeInTheDocument();
	});
});
