import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { AssociationHome } from "@/features/association/association-home";
import type { AssociationHomeData } from "@/features/association/association-loader";

import {
	associationMe,
	collectedReservation,
	fartherSupplier,
	firstPage,
	laterReservation,
	nearbySupplier,
	soonReservation,
} from "../../fixtures/association";
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

		it("gives what, where and the booked pickup time", async () => {
			renderHome();

			const list = await screen.findByRole("list", {
				name: "Collectes à venir",
			});
			const soonest = within(list).getAllByRole("listitem")[0];
			expect(soonest).toHaveTextContent("12 portions");
			expect(soonest).toHaveTextContent("Réfrigéré");
			expect(soonest).toHaveTextContent("Cantine du lycée Ampère");
			expect(soonest).toHaveTextContent("mar. 3 nov. à 15:15");
		});

		it("keeps the pickup code for the collection page", async () => {
			renderHome();

			const list = await screen.findByRole("list", {
				name: "Collectes à venir",
			});
			expect(list).not.toHaveTextContent("482 913");
			expect(
				within(list).getByRole("link", { name: /Hachis parmentier/ }),
			).toHaveAttribute("href", "/association/reservations/3");
		});

		it("leaves the collected reservations to the history page", async () => {
			renderHome();

			expect(
				await screen.findByRole("link", { name: "Historique des collectes" }),
			).toHaveAttribute("href", "/association/history");
			expect(screen.queryByText("Pain de campagne")).not.toBeInTheDocument();
		});

		it("says when no collection is planned", async () => {
			renderHome({ reservations: [] });

			expect(
				await screen.findByText("Aucune collecte prévue pour l'instant."),
			).toBeInTheDocument();
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

		it("switches between the list and the map on the same page", async () => {
			renderHome();

			await userEvent.click(
				await screen.findByRole("button", { name: "Carte" }),
			);

			expect(
				screen.getByRole("group", { name: "Carte des fournisseurs" }),
			).toBeInTheDocument();
			expect(
				screen.queryByRole("list", { name: "Fournisseurs autour de vous" }),
			).not.toBeInTheDocument();
			expect(screen.getByRole("button", { name: "Carte" })).toHaveAttribute(
				"aria-pressed",
				"true",
			);

			await userEvent.click(screen.getByRole("button", { name: "Liste" }));

			expect(
				screen.getByRole("list", { name: "Fournisseurs autour de vous" }),
			).toBeInTheDocument();
		});

		it("offers other search radiuses and marks the current one", async () => {
			renderHome();

			const radiuses = await screen.findByRole("navigation", {
				name: "Rayon de recherche",
			});
			expect(
				within(radiuses).getByRole("link", { name: "10 km" }),
			).toHaveAttribute("aria-current", "page");
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
});
