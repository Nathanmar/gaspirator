import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { SuppliersMap } from "@/features/association/suppliers-map";

import {
	associationMe,
	fartherSupplier,
	nearbySupplier,
} from "../../fixtures/association";
import { renderWithRouter } from "../../utils/render-with-router";

function renderMap() {
	return renderWithRouter(
		<SuppliersMap
			center={associationMe.association.location}
			suppliers={[nearbySupplier, fartherSupplier]}
			radius={10}
		/>,
		{ path: "/association" },
	);
}

const position = (element: HTMLElement) => ({
	left: Number.parseFloat(element.style.left),
	top: Number.parseFloat(element.style.top),
});

describe("SuppliersMap", () => {
	it("puts the association at the centre", async () => {
		renderMap();

		const map = await screen.findByRole("group", {
			name: "Carte des fournisseurs",
		});
		expect(within(map).getByText("Vous")).toBeInTheDocument();
	});

	it("places each supplier in its direction from the association", async () => {
		renderMap();

		// The canteen is north of the association, the hospital south-east.
		const canteen = await screen.findByRole("button", {
			name: /Cantine du lycée Ampère/,
		});
		const hospital = screen.getByRole("button", {
			name: /Hôpital Édouard-Herriot/,
		});
		expect(position(canteen).top).toBeLessThan(50);
		expect(position(hospital).left).toBeGreaterThan(50);
		expect(position(hospital).top).toBeGreaterThan(50);
	});

	it("shows the nearest supplier first, then the one tapped", async () => {
		renderMap();

		const details = await screen.findByRole("region", {
			name: "Fournisseur sélectionné",
		});
		expect(details).toHaveTextContent("Cantine du lycée Ampère");

		const hospital = screen.getByRole("button", {
			name: /Hôpital Édouard-Herriot/,
		});
		await userEvent.click(hospital);

		expect(hospital).toHaveAttribute("aria-pressed", "true");
		expect(details).toHaveTextContent("Hôpital Édouard-Herriot");
		expect(details).toHaveTextContent("4,3 km");
		expect(
			within(details).getByRole("link", { name: /04 72 11 73 11/ }),
		).toHaveAttribute("href", "tel:0472117311");
	});
});
