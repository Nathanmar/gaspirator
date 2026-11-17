import { formatAddress, formatDistance, pluralize } from "@/lib/format";
import { SUPPLIER_TYPE_LABELS } from "@/lib/labels";

import type { SupplierSearchResult } from "./association-api";
import { labelClass, PhoneLink } from "./space-ui";

export function SupplierCard({ supplier }: { supplier: SupplierSearchResult }) {
	const lots = supplier.available_lots_count;

	return (
		<div className="glass flex h-full flex-col rounded-[28px] p-5">
			<div className="flex items-start justify-between gap-3">
				<div className="min-w-0">
					<p className={labelClass}>
						{SUPPLIER_TYPE_LABELS[supplier.supplier_type]}
					</p>
					<p className="mt-1 text-xl leading-tight font-bold tracking-[-0.02em] wrap-anywhere">
						{supplier.name}
					</p>
				</div>
				<p className="shrink-0 rounded-full bg-lime px-3 py-1 text-sm font-semibold text-ink">
					{formatDistance(supplier.distance_km)}
				</p>
			</div>

			<p className="mt-2 text-sm text-cream/70">
				{formatAddress(supplier.address)}
			</p>

			<div className="mt-auto flex flex-wrap items-center justify-between gap-3 pt-4">
				<p className="font-semibold text-lime">
					{pluralize(lots, "lot disponible", "lots disponibles")}
				</p>
				<PhoneLink phone={supplier.contact_phone} />
			</div>
		</div>
	);
}
