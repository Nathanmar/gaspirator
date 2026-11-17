import { Minus, Plus } from "lucide-react";
import { type ReactNode, useEffect, useRef } from "react";

import { cn } from "@/lib/utils";

import type { createReserveMap, LngLat, MapPin } from "./create-reserve-map";

/** Square dark button laid over the map. */
export const mapButtonClass =
	"grid size-11 place-items-center rounded-xl border border-cream/10 bg-ink/85 text-cream backdrop-blur-md transition-colors hover:bg-ink disabled:opacity-40";

/** Dark row over the bottom of the map, for the selected place. */
export const mapRowClass =
	"absolute inset-x-2 bottom-2 flex items-center justify-between gap-3 rounded-xl border border-cream/10 bg-ink/85 py-2 pr-2 pl-3 backdrop-blur-md";

/**
 * Light map with "Vous" at `origin` and clickable pins; `children` are laid over it. The map (a
 * WebGL context plus tiles) is only created once the card gets close to the screen, and again
 * when the origin, pins or radius change.
 */
export function ReserveMapCard({
	origin,
	pins,
	radiusKm,
	interactive = false,
	selectedId,
	onSelect,
	label,
	className,
	creditClassName = "top-1.5 right-2",
	children,
}: {
	origin: LngLat;
	pins: MapPin[];
	radiusKm?: number;
	interactive?: boolean;
	selectedId: MapPin["id"] | undefined;
	onSelect: (id: MapPin["id"]) => void;
	label?: string;
	className?: string;
	creditClassName?: string;
	children: ReactNode;
}) {
	const mapRef = useRef<HTMLDivElement>(null);
	const handleRef = useRef<ReturnType<typeof createReserveMap>>(null);
	const selectedRef = useRef(selectedId);
	selectedRef.current = selectedId;
	const onSelectRef = useRef(onSelect);
	onSelectRef.current = onSelect;

	useEffect(() => {
		const container = mapRef.current;
		if (!container) return;
		let cancelled = false;
		const load = () =>
			import("./create-reserve-map")
				.then(({ createReserveMap }) => {
					if (!cancelled) {
						handleRef.current = createReserveMap(container, {
							origin,
							pins,
							radiusKm,
							interactive,
							selectedId: selectedRef.current,
							onSelect: (id) => onSelectRef.current(id),
						});
					}
				})
				.catch((error: unknown) =>
					console.warn("Reserve map unavailable", error),
				);
		const cleanup = () => {
			cancelled = true;
			handleRef.current?.remove();
			handleRef.current = null;
		};

		if (typeof IntersectionObserver === "undefined") {
			void load();
			return cleanup;
		}
		const observer = new IntersectionObserver(
			([entry]) => {
				if (!entry.isIntersecting) return;
				observer.disconnect();
				void load();
			},
			{ rootMargin: "100%" },
		);
		observer.observe(container);
		return () => {
			observer.disconnect();
			cleanup();
		};
	}, [origin, pins, radiusKm, interactive]);

	// Selection changed outside the map (e.g. previous / next buttons).
	useEffect(() => {
		handleRef.current?.select(selectedId);
	}, [selectedId]);

	return (
		<fieldset
			className={cn(
				"relative h-full min-h-48 min-w-0 overflow-hidden rounded-2xl border border-cream/10 bg-[#e9e4d8] text-sm",
				className,
			)}
		>
			{label && <legend className="sr-only">{label}</legend>}
			{/* MapLibre forces `position: relative` on its container, so size it explicitly. `isolate`
          keeps the raised (selected) pin under the overlays. */}
			<div ref={mapRef} className="isolate h-full w-full" />
			{/* Map data credit, required by the OpenStreetMap and CARTO licences. */}
			<p
				className={cn(
					"pointer-events-none absolute font-mono text-[8px] tracking-wide text-cream/70",
					creditClassName,
				)}
			>
				© OpenStreetMap · CARTO
			</p>
			{interactive && (
				<div className="absolute top-1/2 right-4 flex -translate-y-1/2 flex-col gap-2 lg:right-8">
					<button
						type="button"
						aria-label="Zoomer"
						onClick={() => handleRef.current?.zoomIn()}
						className={mapButtonClass}
					>
						<Plus className="size-4" aria-hidden="true" />
					</button>
					<button
						type="button"
						aria-label="Dézoomer"
						onClick={() => handleRef.current?.zoomOut()}
						className={mapButtonClass}
					>
						<Minus className="size-4" aria-hidden="true" />
					</button>
				</div>
			)}
			{children}
		</fieldset>
	);
}
