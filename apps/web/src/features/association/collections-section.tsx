import { Clock, MapPin } from "lucide-react";

import {
	formatAddress,
	formatDateTime,
	formatPickupCode,
	formatQuantity,
} from "@/lib/format";

import type { Reservation, Storage } from "./association-api";
import { EmptyState, sectionTitleClass } from "./space-ui";

const STORAGE_LABELS: Record<Storage, string> = {
	ambient: "Ambiant",
	refrigerated: "Réfrigéré",
	frozen: "Surgelé",
};

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
	const collected = reservations.filter(
		(reservation) => reservation.status === "collected",
	);

	return (
		<section aria-labelledby="collections-title">
			<h2 id="collections-title" className={sectionTitleClass}>
				Collectes à venir
			</h2>

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
					Vos prochaines collectes et leur code s'afficheront ici.
				</EmptyState>
			)}

			{collected.length > 0 && (
				<>
					<h3
						id="collected-title"
						className="mt-8 text-xs font-semibold tracking-[0.14em] text-cream/70 uppercase"
					>
						Déjà collectées
					</h3>
					<ul
						aria-labelledby="collected-title"
						className="mt-2 divide-y divide-cream/10"
					>
						{collected.map((reservation) => (
							<CollectedReservation
								key={reservation.id}
								reservation={reservation}
							/>
						))}
					</ul>
				</>
			)}
		</section>
	);
}

function UpcomingCollection({ reservation }: { reservation: Reservation }) {
	const { lot, quantity, pickup_at, pickup_code } = reservation;

	return (
		<li className="glass rounded-[28px] p-5">
			<div className="flex items-start justify-between gap-3">
				<div className="min-w-0">
					<p className="text-xl leading-tight font-bold tracking-[-0.02em] wrap-anywhere">
						{lot.title}
					</p>
					<p className="mt-1 text-cream/70">
						{formatQuantity(quantity, lot.unit)}
					</p>
				</div>
				<p className="shrink-0 rounded-full border border-cream/15 px-3 py-1 text-xs font-semibold">
					{STORAGE_LABELS[lot.storage]}
				</p>
			</div>

			<div className="mt-4 grid gap-2 text-sm">
				<p className="flex gap-2">
					<Clock className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
					<span>
						Passage le{" "}
						<span className="font-semibold">{formatDateTime(pickup_at)}</span>
					</span>
				</p>
				<p className="flex gap-2">
					<MapPin className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
					<span>
						<span className="font-semibold">{lot.supplier.name}</span>
						<br />
						<span className="text-cream/70">
							{formatAddress(lot.supplier.address)}
						</span>
					</span>
				</p>
			</div>

			{pickup_code && (
				<div className="mt-5 flex flex-wrap items-center justify-between gap-x-4 gap-y-1 rounded-2xl bg-cream px-5 py-4 text-ink">
					<p className="text-xs font-semibold tracking-[0.14em] uppercase opacity-70">
						Code de collecte
					</p>
					<p className="text-3xl font-extrabold tracking-[0.08em] tabular-nums">
						{formatPickupCode(pickup_code)}
					</p>
				</div>
			)}
		</li>
	);
}

function CollectedReservation({ reservation }: { reservation: Reservation }) {
	const { lot, quantity, collected_at, pickup_at } = reservation;

	return (
		<li className="flex flex-col gap-1 py-3">
			<p>
				<span className="font-semibold">{lot.title}</span>
				<span className="text-cream/70">
					{" "}
					· {formatQuantity(quantity, lot.unit)} · {lot.supplier.name}
				</span>
			</p>
			<p className="text-sm text-cream/70">
				Collectée le {formatDateTime(collected_at ?? pickup_at)}
			</p>
		</li>
	);
}
