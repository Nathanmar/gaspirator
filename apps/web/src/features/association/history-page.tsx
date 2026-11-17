import { formatDateTime, formatQuantity } from "@/lib/format";

import type { Reservation } from "./association-api";
import { BackLink, EmptyState, eyebrowClass, pageTitleClass } from "./space-ui";

const collectedAt = (reservation: Reservation) =>
	reservation.collected_at ?? reservation.pickup_at;

const latestFirst = (a: Reservation, b: Reservation) =>
	Date.parse(collectedAt(b)) - Date.parse(collectedAt(a));

export function HistoryPage({ reservations }: { reservations: Reservation[] }) {
	const collected = reservations
		.filter((reservation) => reservation.status === "collected")
		.sort(latestFirst);

	return (
		<div className="max-w-2xl">
			<BackLink to="/association">Mon espace</BackLink>

			<p className={`mt-4 ${eyebrowClass}`}>Espace association</p>
			<h1 id="history-title" className={pageTitleClass}>
				Historique des collectes
			</h1>

			{collected.length > 0 ? (
				<ul
					aria-labelledby="history-title"
					className="mt-8 divide-y divide-cream/10"
				>
					{collected.map((reservation) => (
						<li key={reservation.id} className="flex flex-col gap-1 py-4">
							<p>
								<span className="font-semibold">{reservation.lot.title}</span>
								<span className="text-cream/70">
									{" "}
									· {formatQuantity(reservation.quantity, reservation.lot.unit)}{" "}
									· {reservation.lot.supplier.name}
								</span>
							</p>
							<p className="text-sm text-cream/70">
								Collectée le {formatDateTime(collectedAt(reservation))}
							</p>
						</li>
					))}
				</ul>
			) : (
				<EmptyState title="Aucune collecte terminée pour l'instant." />
			)}
		</div>
	);
}
