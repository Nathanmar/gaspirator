import { createFileRoute } from "@tanstack/react-router";

import { loadReservation } from "@/features/association/association-loader";
import { PageError, PagePending } from "@/features/association/page-states";
import { ReservationPage } from "@/features/association/reservation-page";

export const Route = createFileRoute(
	"/association/reservations/$reservationId",
)({
	params: {
		parse: ({ reservationId }) => ({ reservationId: Number(reservationId) }),
		stringify: ({ reservationId }) => ({
			reservationId: String(reservationId),
		}),
	},
	loader: ({ params }) => loadReservation(params.reservationId),
	head: ({ loaderData }) => ({
		meta: [{ title: `${loaderData?.lot.title ?? "Collecte"} - Gaspirator` }],
	}),
	pendingComponent: PagePending,
	errorComponent: PageError,
	component: ReservationRoute,
});

function ReservationRoute() {
	return <ReservationPage reservation={Route.useLoaderData()} />;
}
