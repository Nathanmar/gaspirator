import { createFileRoute } from "@tanstack/react-router";

import { AssociationHome } from "@/features/association/association-home";
import {
	associationSearchSchema,
	DEFAULT_RADIUS_KM,
	loadAssociationHome,
} from "@/features/association/association-loader";
import { PageError, PagePending } from "@/features/association/page-states";

export const Route = createFileRoute("/association/")({
	validateSearch: associationSearchSchema,
	loaderDeps: ({ search }) => ({
		radius: search.radius_km ?? DEFAULT_RADIUS_KM,
	}),
	loader: ({ deps }) => loadAssociationHome(deps.radius),
	head: () => ({ meta: [{ title: "Espace association - Gaspirator" }] }),
	pendingComponent: PagePending,
	errorComponent: PageError,
	component: AssociationHomeRoute,
});

function AssociationHomeRoute() {
	const { account } = Route.useRouteContext();
	const data = Route.useLoaderData();
	const { radius } = Route.useLoaderDeps();
	return <AssociationHome data={{ ...account, ...data }} radius={radius} />;
}
