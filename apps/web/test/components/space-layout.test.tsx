import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { SpaceLayout } from "@/components/space-layout";
import { useAuthStore } from "@/features/auth/auth-store";

import { tokens } from "../fixtures/auth";
import { mockFetch } from "../utils/fetch";
import { renderWithRouter } from "../utils/render-with-router";

beforeEach(() => {
	useAuthStore.setState({ tokens });
});

describe("SpaceLayout", () => {
	it("shows the page of the space", async () => {
		renderWithRouter(
			<SpaceLayout>
				<p>Contenu</p>
			</SpaceLayout>,
			{ path: "/association" },
		);

		expect(await screen.findByText("Contenu")).toBeInTheDocument();
	});

	it("logs out from the account menu and goes back to the home page", async () => {
		mockFetch(new Response(null, { status: 204 }));
		const router = renderWithRouter(<SpaceLayout>{null}</SpaceLayout>, {
			path: "/association",
		});

		await userEvent.click(
			await screen.findByRole("button", { name: "Mon compte" }),
		);
		await userEvent.click(
			await screen.findByRole("menuitem", { name: "Se déconnecter" }),
		);

		await waitFor(() => expect(router.state.location.pathname).toBe("/"));
		expect(useAuthStore.getState().tokens).toBeNull();
	});
});
