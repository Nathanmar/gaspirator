import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Reservation } from "@/features/association/association-api";
import { HistoryPage } from "@/features/association/history-page";

import {
	collectedReservation,
	soonReservation,
} from "../../fixtures/association";
import { renderWithRouter } from "../../utils/render-with-router";

const olderCollection: Reservation = {
	...collectedReservation,
	id: 1,
	lot: { ...collectedReservation.lot, id: 39, title: "Soupe de légumes" },
	collected_at: "2026-10-20T11:30:00Z",
};

function renderHistory(reservations: Reservation[]) {
	return renderWithRouter(<HistoryPage reservations={reservations} />, {
		path: "/association/history",
	});
}

describe("HistoryPage", () => {
	it("lists the collected reservations only, the latest first", async () => {
		renderHistory([soonReservation, olderCollection, collectedReservation]);

		const list = await screen.findByRole("list", {
			name: "Historique des collectes",
		});
		const items = within(list).getAllByRole("listitem");
		expect(items).toHaveLength(2);
		expect(items[0]).toHaveTextContent("Pain de campagne");
		expect(items[0]).toHaveTextContent("3,5 kg");
		expect(items[0]).toHaveTextContent("Cantine du lycée Ampère");
		expect(items[0]).toHaveTextContent("Collectée le dim. 1 nov. à 18:05");
		expect(items[1]).toHaveTextContent("Soupe de légumes");
	});

	it("says when nothing has been collected yet", async () => {
		renderHistory([soonReservation]);

		expect(
			await screen.findByText("Aucune collecte terminée pour l'instant."),
		).toBeInTheDocument();
	});

	it("leads back to the association space", async () => {
		renderHistory([]);

		expect(
			await screen.findByRole("link", { name: "Mon espace" }),
		).toHaveAttribute("href", "/association");
	});
});
