import { ArrowUpRight, CircleCheck, Clock, MapPin } from "lucide-react";

import type { GeoPoint } from "@/features/auth/auth-api";
import {
	formatAddress,
	formatDate,
	formatDateTime,
	formatPickupCode,
	formatPickupWindow,
	formatQuantity,
} from "@/lib/format";
import { STORAGE_LABELS } from "@/lib/labels";

import type { Reservation } from "./association-api";
import { LotImage } from "./lot-image";
import {
	BackLink,
	eyebrowClass,
	labelClass,
	PhoneLink,
	pageTitleClass,
	pillLinkClass,
} from "./space-ui";

// Google Maps universal link: opens the app on a phone, the website elsewhere.
function directionsUrl({ latitude, longitude }: GeoPoint) {
	return `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`;
}

export function ReservationPage({ reservation }: { reservation: Reservation }) {
	const { lot, quantity, pickup_at, pickup_code, collected_at } = reservation;
	const isBooked = reservation.status === "booked";

	return (
		<div className="max-w-2xl">
			<BackLink to="/association">Mes collectes</BackLink>

			<LotImage
				lot={lot}
				className="mt-4 h-36 rounded-[28px] md:h-44"
				iconClassName="size-12"
			/>

			<p className={`mt-6 ${eyebrowClass}`}>
				{isBooked ? "Collecte à venir" : "Collecte terminée"}
			</p>
			<h1 className={pageTitleClass}>{lot.title}</h1>
			<p className="mt-4 text-base leading-snug text-cream/70 md:text-lg">
				{formatQuantity(quantity, lot.unit)} · {STORAGE_LABELS[lot.storage]} · À
				consommer jusqu'au {formatDate(lot.use_by_date)}
			</p>

			{isBooked && pickup_code && (
				<div className="mt-8 rounded-[28px] bg-cream px-6 py-7 text-center text-ink">
					<p className="text-xs font-semibold tracking-[0.14em] uppercase opacity-70">
						Code de collecte
					</p>
					<p className="mt-2 text-5xl font-extrabold tracking-[0.1em] tabular-nums md:text-6xl">
						{formatPickupCode(pickup_code)}
					</p>
					<p className="mt-3 text-sm opacity-70">
						Montrez ce code au fournisseur quand vous récupérez le lot.
					</p>
				</div>
			)}

			{!isBooked && collected_at && (
				<p className="mt-8 inline-flex items-center gap-2 rounded-full bg-lime px-4 py-2 font-semibold text-ink">
					<CircleCheck className="size-5" aria-hidden="true" />
					Collectée le {formatDateTime(collected_at)}
				</p>
			)}

			<dl className="glass mt-6 grid gap-5 rounded-[28px] p-5 sm:p-6">
				<div>
					<dt className={`flex items-center gap-2 ${labelClass}`}>
						<Clock className="size-4" aria-hidden="true" />
						Passage prévu
					</dt>
					<dd className="mt-1">
						<p className="text-lg font-semibold">{formatDateTime(pickup_at)}</p>
						<p className="text-sm text-cream/70">
							Créneau du fournisseur&nbsp;:{" "}
							{formatPickupWindow(lot.pickup_start, lot.pickup_end)}
						</p>
					</dd>
				</div>
				<div>
					<dt className={`flex items-center gap-2 ${labelClass}`}>
						<MapPin className="size-4" aria-hidden="true" />
						Chez
					</dt>
					<dd className="mt-1">
						<p className="text-lg font-semibold">{lot.supplier.name}</p>
						<p className="text-cream/70">
							{formatAddress(lot.supplier.address)}
						</p>
						<div className="mt-4 flex flex-wrap gap-3">
							{isBooked && (
								<a
									href={directionsUrl(lot.supplier.location)}
									target="_blank"
									rel="noopener noreferrer"
									className={pillLinkClass}
								>
									<ArrowUpRight className="size-4" aria-hidden="true" />
									Itinéraire
								</a>
							)}
							<PhoneLink phone={lot.supplier.contact_phone} />
						</div>
					</dd>
				</div>
			</dl>
		</div>
	);
}
