import { CircleCheck } from "lucide-react";

import {
	formatDateTime,
	formatMonth,
	formatQuantity,
	pluralize,
} from "@/lib/format";
import { cn } from "@/lib/utils";

import type { QuantityUnit, Reservation } from "./association-api";
import { LotImage } from "./lot-image";
import {
	BackLink,
	EmptyState,
	eyebrowClass,
	pageTitleClass,
	sectionTitleClass,
} from "./space-ui";

const UNITS: QuantityUnit[] = ["portions", "kg", "pieces"];

const collectedAt = (reservation: Reservation) =>
	reservation.collected_at ?? reservation.pickup_at;

const latestFirst = (a: Reservation, b: Reservation) =>
	Date.parse(collectedAt(b)) - Date.parse(collectedAt(a));

/** Reservations grouped by month of collection, in the order received. */
function byMonth(reservations: Reservation[]) {
	const months = new Map<string, Reservation[]>();
	for (const reservation of reservations) {
		const month = formatMonth(collectedAt(reservation));
		const items = months.get(month) ?? [];
		items.push(reservation);
		months.set(month, items);
	}
	return [...months];
}

export function HistoryPage({ reservations }: { reservations: Reservation[] }) {
	const collected = reservations
		.filter((reservation) => reservation.status === "collected")
		.sort(latestFirst);

	return (
		<div className="max-w-2xl">
			<BackLink to="/association">Mon espace</BackLink>

			<p className={`mt-4 ${eyebrowClass}`}>Espace association</p>
			<h1 className={pageTitleClass}>Historique des collectes</h1>

			{collected.length > 0 ? (
				<>
					<Summary collected={collected} />
					{byMonth(collected).map(([month, items]) => (
						<MonthSection key={month} month={month} reservations={items} />
					))}
				</>
			) : (
				<EmptyState title="Aucune collecte terminée pour l'instant." />
			)}
		</div>
	);
}

function Summary({ collected }: { collected: Reservation[] }) {
	const totals = UNITS.map((unit) => ({
		unit,
		amount: collected
			.filter((reservation) => reservation.lot.unit === unit)
			.reduce((sum, reservation) => sum + reservation.quantity, 0),
	})).filter(({ amount }) => amount > 0);

	const tiles = [
		pluralize(collected.length, "collecte", "collectes"),
		...totals.map(({ unit, amount }) => formatQuantity(amount, unit)),
	];

	return (
		<section
			aria-label="Bilan"
			className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4"
		>
			{tiles.map((tile, index) => (
				<p
					key={tile}
					className={cn(
						"rounded-3xl px-4 py-4 text-xl leading-tight font-extrabold tracking-[-0.02em]",
						index === 0 ? "bg-lime text-ink" : "glass",
					)}
				>
					{tile}
				</p>
			))}
		</section>
	);
}

function MonthSection({
	month,
	reservations,
}: {
	month: string;
	reservations: Reservation[];
}) {
	const id = `month-${month.replace(/\s/g, "-")}`;

	return (
		<section aria-labelledby={id} className="mt-10">
			<h2 id={id} className={sectionTitleClass}>
				{month}
			</h2>
			<ul aria-labelledby={id} className="mt-4 grid gap-3">
				{reservations.map((reservation) => (
					<li
						key={reservation.id}
						className="glass flex items-center gap-4 rounded-3xl p-3 pr-4"
					>
						<LotImage
							lot={reservation.lot}
							className="size-16 shrink-0 rounded-2xl"
							iconClassName="size-7"
						/>
						<div className="min-w-0 flex-1">
							<p className="font-semibold wrap-anywhere">
								{reservation.lot.title}
							</p>
							<p className="text-sm text-cream/70">
								{formatQuantity(reservation.quantity, reservation.lot.unit)} ·{" "}
								{reservation.lot.supplier.name}
							</p>
							<p className="mt-1 flex items-center gap-1.5 text-xs font-semibold text-lime">
								<CircleCheck className="size-3.5" aria-hidden="true" />
								{formatDateTime(collectedAt(reservation))}
							</p>
						</div>
					</li>
				))}
			</ul>
		</section>
	);
}
