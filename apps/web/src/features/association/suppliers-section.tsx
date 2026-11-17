import { Link } from "@tanstack/react-router";

import type { GeoPoint } from "@/features/auth/auth-api";
import type { Page } from "@/lib/api-client";
import { cn } from "@/lib/utils";

import type { SupplierSearchResult } from "./association-api";
import { RADIUS_OPTIONS } from "./association-loader";
import { labelClass } from "./space-ui";
import { SuppliersMap } from "./suppliers-map";

const segmentClass = (isActive: boolean) =>
	cn(
		"inline-flex items-center rounded-full px-4 py-2 text-sm font-semibold whitespace-nowrap transition-colors",
		isActive
			? "bg-lime text-ink"
			: "text-cream/70 hover:bg-cream/10 hover:text-cream",
	);

/** The map of the suppliers: the whole right half of the screen on large screens. */
export function SuppliersSection({
	suppliers,
	radius,
	center,
}: {
	suppliers: Page<SupplierSearchResult>;
	radius: number;
	center: GeoPoint;
}) {
	return (
		<section
			aria-labelledby="suppliers-title"
			className="-mx-5 h-[80svh] md:-mx-10 lg:fixed lg:inset-y-0 lg:right-0 lg:mx-0 lg:h-auto lg:w-1/2"
		>
			<SuppliersMap
				center={center}
				suppliers={suppliers.data}
				total={suppliers.meta.total}
				radius={radius}
			/>
		</section>
	);
}

export function RadiusPicker({ radius }: { radius: number }) {
	return (
		<div>
			<p id="radius-label" className={labelClass}>
				Rayon de recherche
			</p>
			<nav aria-labelledby="radius-label" className="mt-3 flex flex-wrap gap-1">
				{RADIUS_OPTIONS.map((option) => (
					<Link
						key={option}
						to="/association"
						search={{ radius_km: option }}
						resetScroll={false}
						aria-current={option === radius ? "page" : undefined}
						className={segmentClass(option === radius)}
					>
						{option} km
					</Link>
				))}
			</nav>
		</div>
	);
}
