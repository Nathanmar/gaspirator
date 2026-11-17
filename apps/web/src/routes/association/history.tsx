import { createFileRoute } from "@tanstack/react-router";

import { loadReservationHistory } from "@/features/association/association-loader";
import { HistoryPage } from "@/features/association/history-page";
import { PageError, PagePending } from "@/features/association/page-states";

export const Route = createFileRoute("/association/history")({
	loader: () => loadReservationHistory(),
	head: () => ({ meta: [{ title: "Historique des collectes - Gaspirator" }] }),
	pendingComponent: PagePending,
	errorComponent: PageError,
	component: HistoryRoute,
});

function HistoryRoute() {
	return <HistoryPage reservations={Route.useLoaderData()} />;
}
