import { useState } from "react";

import { formatDistance } from "@/lib/format";
import { cn } from "@/lib/utils";

import type { SupplierSearchResult } from "./association-api";
import { SupplierCard } from "./supplier-card";

type GeoPoint = { latitude: number; longitude: number };

const KM_PER_DEGREE_OF_LATITUDE = 110.574;
// Share of the half-width taken by the search radius: the outer ring stays inside the frame.
const OUTER_RING = 46;

/** Position in % of the square frame, the association at its centre and north up. */
function placeOnMap(center: GeoPoint, point: GeoPoint, radius: number) {
	const kmPerDegreeOfLongitude =
		111.32 * Math.cos((center.latitude * Math.PI) / 180);
	const east = (point.longitude - center.longitude) * kmPerDegreeOfLongitude;
	const north = (point.latitude - center.latitude) * KM_PER_DEGREE_OF_LATITUDE;
	const scale = OUTER_RING / radius;
	const clamp = (value: number) => Math.min(96, Math.max(4, value));
	return { left: clamp(50 + east * scale), top: clamp(50 - north * scale) };
}

/**
 * Suppliers around the association, at their real direction and distance. It holds the place of
 * the interactive map to come: same data in (centre, suppliers, radius), same selection out.
 */
export function SuppliersMap({
	center,
	suppliers,
	radius,
}: {
	center: GeoPoint;
	suppliers: SupplierSearchResult[];
	radius: number;
}) {
	const [selectedId, setSelectedId] = useState<number | null>(null);
	const selected =
		suppliers.find((supplier) => supplier.id === selectedId) ?? suppliers[0];

	return (
		<div className="grid gap-4 md:grid-cols-2 md:items-start">
			<fieldset className="glass relative aspect-square w-full min-w-0 overflow-hidden rounded-[28px]">
				<legend className="sr-only">Carte des fournisseurs</legend>
				{[OUTER_RING, OUTER_RING / 2].map((ring) => (
					<div
						key={ring}
						aria-hidden="true"
						className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-dashed border-cream/20"
						style={{ width: `${ring * 2}%`, height: `${ring * 2}%` }}
					>
						<span className="absolute -top-2.5 left-1/2 -translate-x-1/2 text-[10px] font-semibold text-cream/50">
							{formatDistance(ring === OUTER_RING ? radius : radius / 2)}
						</span>
					</div>
				))}

				{/* Label under the dot: supplier labels sit above theirs, so a supplier next door never hides it. */}
				<div className="pointer-events-none absolute top-1/2 left-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cream ring-2 ring-ink">
					<span
						aria-hidden="true"
						className="radar-ring absolute -inset-2 rounded-full border border-cream/50"
					/>
					<span className="absolute top-full left-1/2 mt-1.5 -translate-x-1/2 rounded-[5px] bg-cream px-1.5 text-[10px] leading-[1.4] font-semibold text-ink">
						Vous
					</span>
				</div>

				{suppliers.map((supplier) => {
					const { left, top } = placeOnMap(center, supplier.location, radius);
					const isSelected = supplier.id === selected?.id;
					return (
						<button
							key={supplier.id}
							type="button"
							aria-label={`${supplier.name}, ${formatDistance(supplier.distance_km)}`}
							aria-pressed={isSelected}
							onClick={() => setSelectedId(supplier.id)}
							className={cn(
								"map-pin absolute -translate-x-1/2 -translate-y-full p-2",
								isSelected && "is-selected z-10",
							)}
							style={{ left: `${left}%`, top: `${top}%` }}
						>
							<span className="map-pin__label">
								{formatDistance(supplier.distance_km)}
							</span>
							<span className="map-pin__dot" />
						</button>
					);
				})}
			</fieldset>

			{selected && (
				<section aria-label="Fournisseur sélectionné">
					<SupplierCard supplier={selected} />
				</section>
			)}
		</div>
	);
}
