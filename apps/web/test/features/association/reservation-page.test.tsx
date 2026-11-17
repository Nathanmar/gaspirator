import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Reservation } from "@/features/association/association-api";
import { ReservationPage } from "@/features/association/reservation-page";

import {
	collectedReservation,
	soonReservation,
} from "../../fixtures/association";
import { renderWithRouter } from "../../utils/render-with-router";

function renderReservation(reservation: Reservation) {
	return renderWithRouter(<ReservationPage reservation={reservation} />, {
		path: `/association/reservations/${reservation.id}`,
	});
}

describe("ReservationPage", () => {
	it("names the lot and how much of it is reserved", async () => {
		renderReservation(soonReservation);

		expect(
			await screen.findByRole("heading", {
				level: 1,
				name: "Hachis parmentier",
			}),
		).toBeInTheDocument();
		expect(screen.getByText(/12 portions/)).toBeInTheDocument();
		expect(screen.getByText(/Réfrigéré/)).toBeInTheDocument();
		expect(
			screen.getByText(/À consommer jusqu'au mer\. 4 nov\./),
		).toBeInTheDocument();
	});

	it("shows the pickup code to give the supplier", async () => {
		renderReservation(soonReservation);

		expect(await screen.findByText("482 913")).toBeInTheDocument();
		expect(
			screen.getByText(/Montrez ce code au fournisseur/),
		).toBeInTheDocument();
	});

	it("says when and where to go", async () => {
		renderReservation(soonReservation);

		expect(
			await screen.findByText("mar. 3 nov., entre 14:00 et 16:00"),
		).toBeInTheDocument();
		expect(screen.getByText("Cantine du lycée Ampère")).toBeInTheDocument();
		expect(
			screen.getByText("31 rue de la Bourse, 69002 Lyon"),
		).toBeInTheDocument();
	});

	it("opens the route to the supplier in a maps app", async () => {
		renderReservation(soonReservation);

		const directions = await screen.findByRole("link", { name: /Itinéraire/ });
		expect(directions).toHaveAttribute(
			"href",
			"https://www.google.com/maps/dir/?api=1&destination=45.7631,4.8357",
		);
		expect(directions).toHaveAttribute("target", "_blank");
	});

	it("lets the association call the supplier", async () => {
		renderReservation(soonReservation);

		expect(
			await screen.findByRole("link", { name: /04 78 00 00 00/ }),
		).toHaveAttribute("href", "tel:0478000000");
	});

	it("leads back to the association space", async () => {
		renderReservation(soonReservation);

		expect(
			await screen.findByRole("link", { name: "Mes collectes" }),
		).toHaveAttribute("href", "/association");
	});

	it("no longer shows the code once collected", async () => {
		renderReservation(collectedReservation);

		expect(
			await screen.findByText("Collectée le dim. 1 nov. à 18:05"),
		).toBeInTheDocument();
		expect(screen.queryByText("730 114")).not.toBeInTheDocument();
		expect(
			screen.queryByRole("link", { name: /Itinéraire/ }),
		).not.toBeInTheDocument();
	});
});
