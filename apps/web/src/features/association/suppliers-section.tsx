import type { GeoPoint } from "@/features/auth/auth-api";
import type { Page } from "@/lib/api-client";

import type { SupplierSearchResult } from "./association-api";
import { SuppliersMap } from "./suppliers-map";

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
			className="-mx-5 h-[80svh] [view-transition-name:suppliers-map] md:-mx-10 lg:fixed lg:inset-y-0 lg:right-0 lg:mx-0 lg:h-auto lg:w-1/2"
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
