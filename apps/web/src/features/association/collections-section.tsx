import { Link } from "@tanstack/react-router";
import { ChevronRight, Clock, MapPin } from "lucide-react";

import { formatDateTime, formatQuantity } from "@/lib/format";
import { STORAGE_LABELS } from "@/lib/labels";

import type { Reservation } from "./association-api";
import { LotImage } from "./lot-image";
import { EmptyState, sectionTitleClass } from "./space-ui";

const byPickupTime = (a: Reservation, b: Reservation) =>
	Date.parse(a.pickup_at) - Date.parse(b.pickup_at);

export function CollectionsSection({
	reservations,
}: {
	reservations: Reservation[];
}) {
	const upcoming = reservations
		.filter((reservation) => reservation.status === "booked")
		.sort(byPickupTime);

	return (
		<section aria-labelledby="collections-title">
			<div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
				<h2 id="collections-title" className={sectionTitleClass}>
					Collectes à venir
				</h2>
				<Link
					to="/association/history"
					className="text-sm font-semibold underline underline-offset-4"
				>
					Historique des collectes
				</Link>
			</div>

			{upcoming.length > 0 ? (
				<ul aria-labelledby="collections-title" className="mt-4 grid gap-4">
					{upcoming.map((reservation) => (
						<UpcomingCollection
							key={reservation.id}
							reservation={reservation}
						/>
					))}
				</ul>
			) : (
				<EmptyState title="Aucune collecte prévue pour l'instant.">
					Vos prochaines collectes s'afficheront ici.
				</EmptyState>
			)}
		</section>
	);
}

function UpcomingCollection({ reservation }: { reservation: Reservation }) {
	const { lot, quantity } = reservation;

	return (
		<li className="glass relative overflow-hidden rounded-[28px] transition-transform has-focus-visible:ring-2 has-focus-visible:ring-lime active:scale-[0.99]">
			<div className="relative">
				<LotImage lot={lot} className="h-28" />
				<p className="absolute top-3 left-3 rounded-full bg-ink/85 px-3 py-1 text-xs font-semibold backdrop-blur-sm">
					{STORAGE_LABELS[lot.storage]}
				</p>
			</div>

			<div className="p-5">
				<div className="flex items-start justify-between gap-3">
					<div className="min-w-0">
						<p className="text-xl leading-tight font-bold tracking-[-0.02em] wrap-anywhere">
							{/* The whole card is the link (`after:inset-0`), named by the lot. */}
							<Link
								to="/association/reservations/$reservationId"
								params={{ reservationId: reservation.id }}
								className="outline-none after:absolute after:inset-0"
							>
								{lot.title}
							</Link>
						</p>
						<p className="mt-1 text-cream/70">
							{formatQuantity(quantity, lot.unit)}
						</p>
					</div>
					<ChevronRight
						className="mt-1 size-5 shrink-0 text-cream/50"
						aria-hidden="true"
					/>
				</div>

				<div className="mt-4 grid gap-2 text-sm">
					<p className="flex gap-2">
						<Clock className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
						<span>
							Passage prévu le{" "}
							<span className="font-semibold">
								{formatDateTime(reservation.pickup_at)}
							</span>
						</span>
					</p>
					<p className="flex gap-2">
						<MapPin className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
						<span>{lot.supplier.name}</span>
					</p>
				</div>
			</div>
		</li>
	);
}
