import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Reservation } from "@/features/association/association-api";
import { HistoryPage } from "@/features/association/history-page";

import {
	collectedReservation,
	soonReservation,
} from "../../fixtures/association";
import { renderWithRouter } from "../../utils/render-with-router";

const sameMonthCollection: Reservation = {
	...collectedReservation,
	id: 5,
	lot: { ...collectedReservation.lot, id: 44, title: "Pommes" },
	quantity: 2,
	collected_at: "2026-11-02T09:00:00Z",
};

const lastMonthCollection: Reservation = {
	...collectedReservation,
	id: 1,
	lot: {
		...collectedReservation.lot,
		id: 39,
		title: "Soupe de légumes",
		unit: "portions",
	},
	quantity: 20,
	collected_at: "2026-10-20T11:30:00Z",
};

function renderHistory(reservations: Reservation[]) {
	return renderWithRouter(<HistoryPage reservations={reservations} />, {
		path: "/association/history",
	});
}

describe("HistoryPage", () => {
	it("groups the collected reservations by month, the latest first", async () => {
		renderHistory([
			soonReservation,
			lastMonthCollection,
			collectedReservation,
			sameMonthCollection,
		]);

		const months = await screen.findAllByRole("heading", { level: 2 });
		expect(months.map((month) => month.textContent)).toEqual([
			"Novembre 2026",
			"Octobre 2026",
		]);

		const november = within(
			screen.getByRole("list", { name: "Novembre 2026" }),
		).getAllByRole("listitem");
		expect(november).toHaveLength(2);
		expect(november[0]).toHaveTextContent("Pommes");
		expect(november[1]).toHaveTextContent("Pain de campagne");

		const october = within(
			screen.getByRole("list", { name: "Octobre 2026" }),
		).getAllByRole("listitem");
		expect(october).toHaveLength(1);
		expect(october[0]).toHaveTextContent("Soupe de légumes");
	});

	it("gives what was collected, from whom and when", async () => {
		renderHistory([collectedReservation]);

		const [item] = within(
			await screen.findByRole("list", { name: "Novembre 2026" }),
		).getAllByRole("listitem");
		expect(item).toHaveTextContent("Pain de campagne");
		expect(item).toHaveTextContent("3,5 kg");
		expect(item).toHaveTextContent("Cantine du lycée Ampère");
		expect(item).toHaveTextContent("dim. 1 nov. à 18:05");
	});

	it("sums up the collections, with a total per unit", async () => {
		renderHistory([
			lastMonthCollection,
			collectedReservation,
			sameMonthCollection,
		]);

		const summary = await screen.findByRole("region", { name: "Bilan" });
		expect(summary).toHaveTextContent("3 collectes");
		expect(summary).toHaveTextContent("20 portions");
		expect(summary).toHaveTextContent("5,5 kg");
		expect(summary).not.toHaveTextContent("pièce");
	});

	it("says when nothing has been collected yet", async () => {
		renderHistory([soonReservation]);

		expect(
			await screen.findByText("Aucune collecte terminée pour l'instant."),
		).toBeInTheDocument();
		expect(
			screen.queryByRole("region", { name: "Bilan" }),
		).not.toBeInTheDocument();
	});

	it("leads back to the association space", async () => {
		renderHistory([]);

		expect(
			await screen.findByRole("link", { name: "Mon espace" }),
		).toHaveAttribute("href", "/association");
	});
});
