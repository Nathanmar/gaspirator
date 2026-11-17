import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { AssociationHome } from "@/features/association/association-home";
import type { AssociationHomeData } from "@/features/association/association-loader";
import { useAuthStore } from "@/features/auth/auth-store";

import {
	associationMe,
	collectedReservation,
	fartherSupplier,
	firstPage,
	laterReservation,
	nearbySupplier,
	soonReservation,
} from "../../fixtures/association";
import { tokens } from "../../fixtures/auth";
import { mockFetch } from "../../utils/fetch";
import { renderWithRouter } from "../../utils/render-with-router";

const home: AssociationHomeData = {
	firstname: "Marie",
	association: associationMe.association,
	// API order: most recently booked first.
	reservations: [laterReservation, soonReservation, collectedReservation],
	suppliers: firstPage([nearbySupplier, fartherSupplier]),
};

function renderHome(data: Partial<AssociationHomeData> = {}, radius = 10) {
	return renderWithRouter(
		<AssociationHome data={{ ...home, ...data }} radius={radius} />,
		{ path: "/association" },
	);
}

beforeEach(() => {
	useAuthStore.setState({ tokens });
});

describe("AssociationHome", () => {
	it("greets the manager and names the association", async () => {
		renderHome();

		expect(
			await screen.findByRole("heading", { level: 1, name: "Bonjour Marie" }),
		).toBeInTheDocument();
		expect(screen.getByText(/Restos du Cœur Lyon 2/)).toBeInTheDocument();
	});

	describe("collections", () => {
		it("lists the upcoming collections, soonest first", async () => {
			renderHome();

			const list = await screen.findByRole("list", {
				name: "Collectes à venir",
			});
			const items = within(list).getAllByRole("listitem");
			expect(items).toHaveLength(2);
			expect(items[0]).toHaveTextContent("Hachis parmentier");
			expect(items[1]).toHaveTextContent("Yaourts nature");
		});

		it("gives what, where, when, and the pickup code to show the supplier", async () => {
			renderHome();

			const list = await screen.findByRole("list", {
				name: "Collectes à venir",
			});
			const soonest = within(list).getAllByRole("listitem")[0];
			expect(soonest).toHaveTextContent("12 portions");
			expect(soonest).toHaveTextContent("Réfrigéré");
			expect(soonest).toHaveTextContent("Cantine du lycée Ampère");
			expect(soonest).toHaveTextContent("31 rue de la Bourse, 69002 Lyon");
			expect(soonest).toHaveTextContent("mar. 3 nov. à 15:15");
			expect(soonest).toHaveTextContent("Code de collecte");
			expect(soonest).toHaveTextContent("482 913");
		});

		it("keeps the collected reservations apart, without their code", async () => {
			renderHome();

			const list = await screen.findByRole("list", { name: "Déjà collectées" });
			const item = within(list).getByRole("listitem");
			expect(item).toHaveTextContent("Pain de campagne");
			expect(item).toHaveTextContent("3,5 kg");
			expect(item).toHaveTextContent("Collectée le dim. 1 nov. à 18:05");
			expect(item).not.toHaveTextContent("730 114");
		});

		it("says when no collection is planned", async () => {
			renderHome({ reservations: [] });

			expect(
				await screen.findByText("Aucune collecte prévue pour l'instant."),
			).toBeInTheDocument();
			expect(
				screen.queryByRole("list", { name: "Déjà collectées" }),
			).not.toBeInTheDocument();
		});
	});

	describe("suppliers around", () => {
		it("lists the suppliers with lots to give, nearest first", async () => {
			renderHome();

			const list = await screen.findByRole("list", {
				name: "Fournisseurs autour de vous",
			});
			const items = within(list).getAllByRole("listitem");
			expect(items).toHaveLength(2);
			expect(items[0]).toHaveTextContent("Cantine du lycée Ampère");
			expect(items[0]).toHaveTextContent("Cantine");
			expect(items[0]).toHaveTextContent("350 m");
			expect(items[0]).toHaveTextContent("2 lots disponibles");
			expect(items[0]).toHaveTextContent("31 rue de la Bourse, 69002 Lyon");
			expect(items[1]).toHaveTextContent("Hôpital Édouard-Herriot");
			expect(items[1]).toHaveTextContent("4,3 km");
			expect(items[1]).toHaveTextContent("1 lot disponible");
		});

		it("lets the association call a supplier", async () => {
			renderHome();

			expect(
				await screen.findByRole("link", { name: /04 78 00 00 00/ }),
			).toHaveAttribute("href", "tel:0478000000");
		});

		it("offers other search radiuses and marks the current one", async () => {
			renderHome();

			const radiuses = await screen.findByRole("navigation", {
				name: "Rayon de recherche",
			});
			expect(
				within(radiuses).getByRole("link", { name: "10 km" }),
			).toHaveAttribute("aria-current", "true");
			expect(
				within(radiuses).getByRole("link", { name: "25 km" }),
			).toHaveAttribute("href", "/association?radius_km=25");
		});

		it("suggests a wider radius when no supplier is close enough", async () => {
			renderHome({ suppliers: firstPage([]) });

			expect(
				await screen.findByText(
					"Aucun fournisseur n'a de lot disponible à moins de 10 km.",
				),
			).toBeInTheDocument();
			expect(
				screen.getByRole("link", { name: "Chercher à 25 km" }),
			).toHaveAttribute("href", "/association?radius_km=25");
		});

		it("has no wider radius to suggest at the largest one", async () => {
			renderHome({ suppliers: firstPage([]) }, 50);

			expect(
				await screen.findByText(
					"Aucun fournisseur n'a de lot disponible à moins de 50 km.",
				),
			).toBeInTheDocument();
			expect(
				screen.queryByRole("link", { name: /Chercher à/ }),
			).not.toBeInTheDocument();
		});
	});

	it("logs out and goes back to the home page", async () => {
		mockFetch(new Response(null, { status: 204 }));
		const router = renderHome();

		await userEvent.click(
			await screen.findByRole("button", { name: "Se déconnecter" }),
		);

		await waitFor(() => expect(router.state.location.pathname).toBe("/"));
		expect(useAuthStore.getState().tokens).toBeNull();
	});
});
