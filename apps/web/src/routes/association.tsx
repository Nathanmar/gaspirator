import { createFileRoute } from "@tanstack/react-router";

import {
	AssociationHome,
	AssociationHomeError,
	AssociationHomePending,
} from "@/features/association/association-home";
import {
	associationSearchSchema,
	DEFAULT_RADIUS_KM,
	loadAssociationHome,
} from "@/features/association/association-loader";
import { requireLogin } from "@/features/auth/auth-guard";

export const Route = createFileRoute("/association")({
	validateSearch: associationSearchSchema,
	beforeLoad: () => requireLogin("association"),
	loaderDeps: ({ search }) => ({
		radius: search.radius_km ?? DEFAULT_RADIUS_KM,
	}),
	loader: ({ deps }) => loadAssociationHome(deps.radius),
	head: () => ({ meta: [{ title: "Espace association - Gaspirator" }] }),
	pendingComponent: AssociationHomePending,
	errorComponent: AssociationHomeError,
	component: AssociationRoute,
});

function AssociationRoute() {
	const data = Route.useLoaderData();
	const { radius } = Route.useLoaderDeps();
	return <AssociationHome data={data} radius={radius} />;
}
