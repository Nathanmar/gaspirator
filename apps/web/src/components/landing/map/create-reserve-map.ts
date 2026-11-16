import { getVersion, LngLatBounds, Map, Marker, setWorkerUrl } from "maplibre-gl";

import { RESERVE_ORIGIN, SUPPLIERS, type Supplier } from "../content";

// Served from public/ by the maplibre-worker plugin in vite.config.ts; the version busts stale caches.
setWorkerUrl(`/maplibre/maplibre-gl-worker.mjs?v=${getVersion()}`);

// Same look as the Splits events map: CARTO Dark Matter (OpenStreetMap data).
const STYLE_URL = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

function supplierPin(supplier: Supplier) {
  const element = document.createElement("button");
  element.type = "button";
  element.className = "map-pin";
  element.innerHTML = `<span class="map-pin__label">${supplier.shortName}</span><span class="map-pin__dot"></span>`;
  return element;
}

function originPin() {
  const element = document.createElement("div");
  element.className = "map-pin is-origin";
  element.innerHTML = `<span class="map-pin__label">Vous</span><span class="map-pin__dot"></span>`;
  return element;
}

/**
 * Lyon map for the "Réserver" step: supplier pins can be clicked to pick the donation shown under
 * the map. The map itself doesn't pan or zoom so it never fights the page scroll.
 * Returns a cleanup function.
 */
export function createReserveMap(
  container: HTMLElement,
  { selectedId, onSelect }: { selectedId: Supplier["id"]; onSelect: (id: Supplier["id"]) => void },
) {
  const bounds = new LngLatBounds();
  for (const supplier of SUPPLIERS) bounds.extend(supplier.lngLat);

  const map = new Map({
    container,
    style: STYLE_URL,
    bounds,
    // Room for the labels around the dots (half a label on each side), and for the donation row
    // over the bottom of the map.
    fitBoundsOptions: { padding: { top: 32, bottom: 64, left: 64, right: 64 } },
    interactive: false,
    attributionControl: false,
    fadeDuration: 0,
  });

  new Marker({ element: originPin(), anchor: "bottom" }).setLngLat(RESERVE_ORIGIN).addTo(map);

  const pins = SUPPLIERS.map((supplier) => {
    // Anchor on the dot (bottom of the element) so the label floats above the place.
    const marker = new Marker({ element: supplierPin(supplier), anchor: "bottom" })
      .setLngLat(supplier.lngLat)
      .addTo(map);
    const element = marker.getElement();
    element.setAttribute("aria-label", `${supplier.name}, ${supplier.portions} portions`);
    element.addEventListener("click", () => {
      select(supplier.id);
      onSelect(supplier.id);
    });
    return { id: supplier.id, element };
  });

  function select(id: Supplier["id"]) {
    for (const pin of pins) {
      const selected = pin.id === id;
      pin.element.classList.toggle("is-selected", selected);
      pin.element.setAttribute("aria-pressed", String(selected));
      // Keep the selected label above its neighbours.
      pin.element.style.zIndex = selected ? "1" : "";
    }
  }
  select(selectedId);

  return () => map.remove();
}
