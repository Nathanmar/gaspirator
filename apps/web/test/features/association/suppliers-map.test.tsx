import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { createReserveMap } from "@/components/landing/map/create-reserve-map";
import { SuppliersMap } from "@/features/association/suppliers-map";

import {
	associationMe,
	fartherSupplier,
	nearbySupplier,
} from "../../fixtures/association";
import { renderWithRouter } from "../../utils/render-with-router";

// MapLibre needs WebGL, which jsdom lacks: check what the map is given instead.
const handle = {
	remove: vi.fn(),
	select: vi.fn(),
	zoomIn: vi.fn(),
	zoomOut: vi.fn(),
};
const createMap = vi.fn<typeof createReserveMap>(() => handle);
vi.mock("@/components/landing/map/create-reserve-map", () => ({
	createReserveMap: (...args: Parameters<typeof createReserveMap>) =>
		createMap(...args),
}));

beforeEach(() => {
	createMap.mockClear();
	for (const fn of Object.values(handle)) fn.mockClear();
});

function renderMap(suppliers = [nearbySupplier, fartherSupplier], radius = 10) {
	return renderWithRouter(
		<SuppliersMap
			center={associationMe.association.location}
			suppliers={suppliers}
			total={suppliers.length}
			radius={radius}
		/>,
		{ path: "/association" },
	);
}

async function mapOptions() {
	await waitFor(() => expect(createMap).toHaveBeenCalled());
	return createMap.mock.calls.at(-1)![1];
}

describe("SuppliersMap", () => {
	it("frames the search radius around the association, as a map one can move", async () => {
		renderMap();

		const { origin, radiusKm, interactive } = await mapOptions();
		expect(interactive).toBe(true);
		const { latitude, longitude } = associationMe.association.location;
		expect(origin).toEqual([longitude, latitude]);
		expect(radiusKm).toBe(10);
	});

	it("puts a pin on each supplier", async () => {
		renderMap();

		const { pins } = await mapOptions();
		// \s: formatDistance puts a narrow no-break space before the unit.
		expect(pins).toHaveLength(2);
		expect(pins[0].ariaLabel).toMatch(/^Cantine du lycée Ampère, 350\sm$/);
		expect(pins[1].ariaLabel).toMatch(/^Hôpital Édouard-Herriot, 4,3\skm$/);
	});

	it("counts the suppliers and their lots", async () => {
		renderMap();

		const map = await screen.findByRole("group", {
			name: "Carte des fournisseurs",
		});
		expect(map).toHaveTextContent("2 fournisseurs");
		expect(map).toHaveTextContent("3 lots");
	});

	it("shows the nearest supplier first, then the one tapped", async () => {
		renderMap();

		const details = await screen.findByRole("region", {
			name: "Fournisseur sélectionné",
		});
		expect(details).toHaveTextContent("Cantine du lycée Ampère");

		const { onSelect } = await mapOptions();
		act(() => onSelect(fartherSupplier.id));

		expect(details).toHaveTextContent("Hôpital Édouard-Herriot");
		expect(details).toHaveTextContent("1 lot disponible");
		expect(
			within(details).getByRole("link", { name: /04 72 11 73 11/ }),
		).toHaveAttribute("href", "tel:0472117311");
	});

	it("goes through the suppliers with previous and next, moving the map along", async () => {
		renderMap();

		const details = await screen.findByRole("region", {
			name: "Fournisseur sélectionné",
		});
		await mapOptions();

		await userEvent.click(
			screen.getByRole("button", { name: "Fournisseur suivant" }),
		);
		expect(details).toHaveTextContent("Hôpital Édouard-Herriot");
		expect(handle.select).toHaveBeenLastCalledWith(fartherSupplier.id);

		// Wraps around from the first to the last.
		await userEvent.click(
			screen.getByRole("button", { name: "Fournisseur précédent" }),
		);
		await userEvent.click(
			screen.getByRole("button", { name: "Fournisseur précédent" }),
		);
		expect(details).toHaveTextContent("Hôpital Édouard-Herriot");
	});

	it("zooms with its own buttons", async () => {
		renderMap();
		await mapOptions();

		await userEvent.click(screen.getByRole("button", { name: "Zoomer" }));
		await userEvent.click(screen.getByRole("button", { name: "Dézoomer" }));

		expect(handle.zoomIn).toHaveBeenCalledOnce();
		expect(handle.zoomOut).toHaveBeenCalledOnce();
	});

	it("still shows the map when no supplier is close enough", async () => {
		renderMap([]);

		const map = await screen.findByRole("group", {
			name: "Carte des fournisseurs",
		});
		expect(map).toHaveTextContent(
			"Aucun fournisseur n'a de lot disponible à moins de 10 km.",
		);
		expect((await mapOptions()).pins).toEqual([]);
		expect(
			screen.queryByRole("button", { name: "Fournisseur suivant" }),
		).not.toBeInTheDocument();
	});
});
