import { Link } from "@tanstack/react-router";
import { Phone } from "lucide-react";

import type { Page } from "@/lib/api-client";
import { formatAddress, formatDistance } from "@/lib/format";
import { SUPPLIER_TYPE_LABELS } from "@/lib/labels";
import { cn } from "@/lib/utils";

import type { SupplierSearchResult } from "./association-api";
import { RADIUS_OPTIONS } from "./association-loader";
import { EmptyState, sectionTitleClass } from "./space-ui";

function plural(count: number, one: string, many: string) {
	return `${count} ${count > 1 ? many : one}`;
}

export function SuppliersSection({
	suppliers,
	radius,
}: {
	suppliers: Page<SupplierSearchResult>;
	radius: number;
}) {
	const widerRadius = RADIUS_OPTIONS.find((option) => option > radius);

	return (
		<section aria-labelledby="suppliers-title">
			<div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
				<h2 id="suppliers-title" className={sectionTitleClass}>
					Fournisseurs autour de vous
				</h2>
				<RadiusPicker radius={radius} />
			</div>

			{suppliers.data.length > 0 ? (
				<>
					<p className="mt-2 text-sm text-cream/70">
						{plural(suppliers.meta.total, "fournisseur", "fournisseurs")} avec
						des lots à moins de {radius} km
					</p>
					<ul
						aria-labelledby="suppliers-title"
						className="mt-4 grid gap-4 md:grid-cols-2"
					>
						{suppliers.data.map((supplier) => (
							<SupplierCard key={supplier.id} supplier={supplier} />
						))}
					</ul>
				</>
			) : (
				<EmptyState
					title={`Aucun fournisseur n'a de lot disponible à moins de ${radius} km.`}
				>
					{widerRadius && (
						<Link
							to="/association"
							search={{ radius_km: widerRadius }}
							resetScroll={false}
						>
							Chercher à {widerRadius} km
						</Link>
					)}
				</EmptyState>
			)}
		</section>
	);
}

function RadiusPicker({ radius }: { radius: number }) {
	return (
		<nav
			aria-label="Rayon de recherche"
			className="glass flex rounded-full p-1"
		>
			{RADIUS_OPTIONS.map((option) => (
				<Link
					key={option}
					to="/association"
					search={{ radius_km: option }}
					resetScroll={false}
					aria-current={option === radius ? "page" : undefined}
					className={cn(
						"rounded-full px-3 py-2 text-xs font-semibold whitespace-nowrap transition-colors",
						option === radius
							? "bg-lime text-ink"
							: "text-cream/70 hover:bg-cream/10 hover:text-cream",
					)}
				>
					{option} km
				</Link>
			))}
		</nav>
	);
}

function SupplierCard({ supplier }: { supplier: SupplierSearchResult }) {
	const lots = supplier.available_lots_count;

	return (
		<li className="glass flex flex-col rounded-[28px] p-5">
			<div className="flex items-start justify-between gap-3">
				<div className="min-w-0">
					<p className="text-xs font-semibold tracking-[0.14em] text-cream/70 uppercase">
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
					{plural(lots, "lot disponible", "lots disponibles")}
				</p>
				<a
					href={`tel:${supplier.contact_phone.replace(/[^\d+]/g, "")}`}
					className="inline-flex h-11 items-center gap-2 rounded-full border border-cream/15 px-4 text-sm font-semibold transition-colors hover:bg-cream/10"
				>
					<Phone className="size-4" aria-hidden="true" />
					{supplier.contact_phone}
				</a>
			</div>
		</li>
	);
}
