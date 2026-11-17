import {
	getVersion,
	LngLatBounds,
	Marker,
	Map as ReserveMap,
	setWorkerUrl,
} from "maplibre-gl";

// Served from public/ by the maplibre-worker plugin in vite.config.ts; the version busts stale caches.
setWorkerUrl(`/maplibre/maplibre-gl-worker.mjs?v=${getVersion()}`);

// Same look as the Splits events map: CARTO Dark Matter (OpenStreetMap data).
const STYLE_URL =
	"https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

const KM_PER_DEGREE_OF_LATITUDE = 110.574;

export type LngLat = [number, number];

export interface MapPin {
	id: string | number;
	label: string;
	ariaLabel: string;
	lngLat: LngLat;
}

function pinElement(tag: "button" | "div", label: string, className: string) {
	const element = document.createElement(tag);
	element.className = className;
	const text = document.createElement("span");
	text.className = "map-pin__label";
	// textContent, not innerHTML: labels come from the API.
	text.textContent = label;
	const dot = document.createElement("span");
	dot.className = "map-pin__dot";
	element.append(text, dot);
	return element;
}

/** Square around `origin` that holds a circle of `radiusKm`. */
function radiusBounds([lng, lat]: LngLat, radiusKm: number) {
	const dLat = radiusKm / KM_PER_DEGREE_OF_LATITUDE;
	const dLng = radiusKm / (111.32 * Math.cos((lat * Math.PI) / 180));
	return new LngLatBounds([lng - dLng, lat - dLat], [lng + dLng, lat + dLat]);
}

/**
 * Map of the "Réserver" step: pins can be clicked to pick the place shown under the map. Unless
 * `interactive`, the map doesn't pan or zoom so it never fights the page scroll. It frames the
 * search radius when given, the pins otherwise. Returns a cleanup function.
 */
export function createReserveMap(
	container: HTMLElement,
	{
		origin,
		pins,
		radiusKm,
		interactive = false,
		selectedId,
		onSelect,
	}: {
		origin: LngLat;
		pins: MapPin[];
		radiusKm?: number;
		interactive?: boolean;
		selectedId: MapPin["id"] | undefined;
		onSelect: (id: MapPin["id"]) => void;
	},
) {
	let bounds: LngLatBounds;
	if (radiusKm) {
		bounds = radiusBounds(origin, radiusKm);
	} else {
		bounds = new LngLatBounds(origin, origin);
		for (const pin of pins) bounds.extend(pin.lngLat);
	}

	const map = new ReserveMap({
		container,
		style: STYLE_URL,
		bounds,
		// Room for the labels around the dots (half a label on each side), and for the row over the
		// bottom of the map.
		fitBoundsOptions: { padding: { top: 32, bottom: 64, left: 64, right: 64 } },
		interactive,
		dragRotate: false,
		attributionControl: false,
		fadeDuration: 0,
	});
	if (interactive) map.touchZoomRotate.disableRotation();

	new Marker({
		element: pinElement("div", "Vous", "map-pin is-origin"),
		anchor: "bottom",
	})
		.setLngLat(origin)
		.addTo(map);

	const markers = pins.map((pin) => {
		// Anchor on the dot (bottom of the element) so the label floats above the place.
		const element = pinElement("button", pin.label, "map-pin");
		(element as HTMLButtonElement).type = "button";
		element.setAttribute("aria-label", pin.ariaLabel);
		element.addEventListener("click", () => {
			select(pin.id);
			onSelect(pin.id);
		});
		new Marker({ element, anchor: "bottom" }).setLngLat(pin.lngLat).addTo(map);
		return { id: pin.id, element, lngLat: pin.lngLat };
	});

	function select(id: MapPin["id"] | undefined) {
		for (const marker of markers) {
			const selected = marker.id === id;
			marker.element.classList.toggle("is-selected", selected);
			marker.element.setAttribute("aria-pressed", String(selected));
			// Keep the selected label above its neighbours.
			marker.element.style.zIndex = selected ? "1" : "";
		}
	}
	select(selectedId);

	return {
		remove: () => map.remove(),
		zoomIn: () => map.zoomIn(),
		zoomOut: () => map.zoomOut(),
		/** Selection made outside the map (previous / next): brings the pin into view if needed. */
		select(id: MapPin["id"] | undefined) {
			select(id);
			const marker = markers.find((m) => m.id === id);
			if (interactive && marker && !map.getBounds().contains(marker.lngLat)) {
				map.easeTo({ center: marker.lngLat });
			}
		},
	};
}
