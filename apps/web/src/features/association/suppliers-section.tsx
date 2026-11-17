import { Link } from "@tanstack/react-router";
import { List, Map as MapIcon } from "lucide-react";
import { useState } from "react";

import type { Page } from "@/lib/api-client";
import { pluralize } from "@/lib/format";
import { cn } from "@/lib/utils";

import type { SupplierSearchResult } from "./association-api";
import { RADIUS_OPTIONS } from "./association-loader";
import { EmptyState, sectionTitleClass } from "./space-ui";
import { SupplierCard } from "./supplier-card";
import { SuppliersMap } from "./suppliers-map";

type View = "list" | "map";

const segmentClass = (isActive: boolean) =>
	cn(
		"inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-xs font-semibold whitespace-nowrap transition-colors",
		isActive
			? "bg-lime text-ink"
			: "text-cream/70 hover:bg-cream/10 hover:text-cream",
	);

export function SuppliersSection({
	suppliers,
	radius,
	center,
}: {
	suppliers: Page<SupplierSearchResult>;
	radius: number;
	center: { latitude: number; longitude: number };
}) {
	const [view, setView] = useState<View>("list");
	const widerRadius = RADIUS_OPTIONS.find((option) => option > radius);
	const hasSuppliers = suppliers.data.length > 0;

	return (
		<section aria-labelledby="suppliers-title">
			<h2 id="suppliers-title" className={sectionTitleClass}>
				Fournisseurs autour de vous
			</h2>

			<div className="mt-3 flex flex-wrap items-center justify-between gap-3">
				<RadiusPicker radius={radius} />
				{hasSuppliers && (
					<div className="glass flex rounded-full p-1">
						<button
							type="button"
							aria-pressed={view === "list"}
							onClick={() => setView("list")}
							className={segmentClass(view === "list")}
						>
							<List className="size-4" aria-hidden="true" />
							Liste
						</button>
						<button
							type="button"
							aria-pressed={view === "map"}
							onClick={() => setView("map")}
							className={segmentClass(view === "map")}
						>
							<MapIcon className="size-4" aria-hidden="true" />
							Carte
						</button>
					</div>
				)}
			</div>

			{hasSuppliers ? (
				<>
					<p className="mt-3 text-sm text-cream/70">
						{pluralize(suppliers.meta.total, "fournisseur", "fournisseurs")}{" "}
						avec des lots à moins de {radius} km
					</p>
					<div className="mt-4">
						{view === "list" ? (
							<ul
								aria-labelledby="suppliers-title"
								className="grid gap-4 md:grid-cols-2"
							>
								{suppliers.data.map((supplier) => (
									<li key={supplier.id}>
										<SupplierCard supplier={supplier} />
									</li>
								))}
							</ul>
						) : (
							<SuppliersMap
								center={center}
								suppliers={suppliers.data}
								radius={radius}
							/>
						)}
					</div>
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
					className={segmentClass(option === radius)}
				>
					{option} km
				</Link>
			))}
		</nav>
	);
}
