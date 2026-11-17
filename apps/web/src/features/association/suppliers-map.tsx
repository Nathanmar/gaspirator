import { Link } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";

import type { MapPin } from "@/components/landing/map/create-reserve-map";
import {
	mapButtonClass,
	ReserveMapCard,
} from "@/components/landing/map/reserve-map-card";
import type { GeoPoint } from "@/features/auth/auth-api";
import { formatAddress, formatDistance, pluralize } from "@/lib/format";
import { SUPPLIER_TYPE_LABELS } from "@/lib/labels";
import { cn } from "@/lib/utils";

import type { SupplierSearchResult } from "./association-api";
import { RADIUS_OPTIONS } from "./association-loader";
import { labelClass, PhoneLink } from "./space-ui";

const segmentClass = (isActive: boolean) =>
	cn(
		"inline-flex flex-1 items-center justify-center rounded-full px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors",
		isActive
			? "bg-lime text-ink"
			: "text-cream/70 hover:bg-cream/10 hover:text-cream",
	);

function RadiusPicker({ radius }: { radius: number }) {
	return (
		<nav
			aria-label="Rayon de recherche"
			className="mt-3 flex gap-1 rounded-full bg-cream/5 p-1"
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

const panelClass =
	"pointer-events-auto rounded-[28px] border border-cream/10 bg-ink/85 backdrop-blur-md";

/**
 * Suppliers around the association on a map one can move, shown even when there are none: title
 * and counts on top, the selected supplier at the bottom left, previous / next at the bottom right.
 */
export function SuppliersMap({
	center,
	suppliers,
	total,
	radius,
}: {
	center: GeoPoint;
	suppliers: SupplierSearchResult[];
	total: number;
	radius: number;
}) {
	const [selectedId, setSelectedId] = useState<MapPin["id"]>();
	const index = Math.max(
		0,
		suppliers.findIndex((supplier) => supplier.id === selectedId),
	);
	const selected = suppliers.at(index);
	const widerRadius = RADIUS_OPTIONS.find((option) => option > radius);
	const lots = suppliers.reduce((sum, s) => sum + s.available_lots_count, 0);

	// Stable references: the map is recreated when they change.
	const origin = useMemo<[number, number]>(
		() => [center.longitude, center.latitude],
		[center.longitude, center.latitude],
	);
	const pins = useMemo(
		() =>
			suppliers.map((supplier) => ({
				id: supplier.id,
				label: supplier.name,
				ariaLabel: `${supplier.name}, ${formatDistance(supplier.distance_km)}`,
				lngLat: [supplier.location.longitude, supplier.location.latitude] as [
					number,
					number,
				],
			})),
		[suppliers],
	);

	const go = (step: number) =>
		setSelectedId(
			suppliers[(index + step + suppliers.length) % suppliers.length].id,
		);

	return (
		<ReserveMapCard
			origin={origin}
			pins={pins}
			radiusKm={radius}
			interactive
			selectedId={selected?.id}
			onSelect={setSelectedId}
			label="Carte des fournisseurs"
			className="rounded-none border-0"
			creditClassName="bottom-1.5 left-1/2 -translate-x-1/2"
		>
			{/* Top left: the top right is kept for the account buttons of SpaceLayout. */}
			<div
				className={`${panelClass} absolute top-4 left-4 p-4 lg:top-8 lg:left-8`}
			>
				<div className="flex flex-wrap items-baseline justify-between gap-x-5 gap-y-1 px-1">
					<h2 id="suppliers-title" className="font-semibold">
						Fournisseurs autour de vous
					</h2>
					<p className="text-cream/70">
						<span className="font-semibold text-cream">{total}</span>{" "}
						{total > 1 ? "fournisseurs" : "fournisseur"} ·{" "}
						<span className="font-semibold text-lime">{lots}</span>{" "}
						{lots > 1 ? "lots" : "lot"}
					</p>
				</div>
				<RadiusPicker radius={radius} />
			</div>

			<div className="pointer-events-none absolute inset-x-4 bottom-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between lg:inset-x-8 lg:bottom-8">
				{selected ? (
					<section
						aria-label="Fournisseur sélectionné"
						aria-live="polite"
						className={`${panelClass} w-full p-5 sm:max-w-sm`}
					>
						<div
							key={selected.id}
							className="animate-in duration-300 fade-in slide-in-from-bottom-1"
						>
							<div className="flex items-start justify-between gap-3">
								<div className="min-w-0">
									<p className={labelClass}>
										{SUPPLIER_TYPE_LABELS[selected.supplier_type]}
									</p>
									<p className="mt-1 text-xl leading-tight font-bold tracking-[-0.02em] wrap-anywhere">
										{selected.name}
									</p>
								</div>
								<p className="shrink-0 text-3xl leading-none font-bold tracking-[-0.04em]">
									{formatDistance(selected.distance_km)}
								</p>
							</div>
							<p className="mt-2 text-sm text-cream/70">
								{formatAddress(selected.address)}
							</p>
							<div className="mt-4 flex flex-wrap items-center justify-between gap-3">
								<p className="font-semibold text-lime">
									{pluralize(
										selected.available_lots_count,
										"lot disponible",
										"lots disponibles",
									)}
								</p>
								<PhoneLink phone={selected.contact_phone} />
							</div>
						</div>
					</section>
				) : (
					<div className={`${panelClass} w-full p-5 sm:max-w-sm`}>
						<p>
							Aucun fournisseur n'a de lot disponible à moins de {radius} km.
						</p>
						{widerRadius && (
							<Link
								to="/association"
								search={{ radius_km: widerRadius }}
								resetScroll={false}
								className="mt-4 inline-flex rounded-full bg-lime px-4 py-2 text-sm font-semibold text-ink"
							>
								Chercher à {widerRadius} km
							</Link>
						)}
					</div>
				)}

				{suppliers.length > 1 && (
					<div className="pointer-events-auto flex items-center gap-3 self-end">
						<button
							type="button"
							aria-label="Fournisseur précédent"
							onClick={() => go(-1)}
							className={mapButtonClass}
						>
							<ChevronLeft className="size-4" aria-hidden="true" />
						</button>
						<button
							type="button"
							onClick={() => go(1)}
							className="inline-flex h-11 items-center gap-2 rounded-xl border border-cream/10 bg-ink/85 px-4 text-xs font-semibold tracking-[0.18em] text-cream uppercase backdrop-blur-md transition-colors hover:bg-ink"
						>
							Fournisseur suivant
							<ChevronRight className="size-4 text-lime" aria-hidden="true" />
						</button>
					</div>
				)}
			</div>
		</ReserveMapCard>
	);
}
