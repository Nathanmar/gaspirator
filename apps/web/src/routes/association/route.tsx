import { createFileRoute, Outlet } from "@tanstack/react-router";

import { SpaceLayout } from "@/components/space-layout";
import { loadAssociationAccount } from "@/features/association/association-loader";
import { PageError, PagePending } from "@/features/association/page-states";
import { requireLogin } from "@/features/auth/auth-guard";

// Layout of the association space: checks the session and the association once, before the
// pages below load their own data.
export const Route = createFileRoute("/association")({
	beforeLoad: async () => {
		requireLogin("association");
		return { account: await loadAssociationAccount() };
	},
	pendingComponent: () => (
		<SpaceLayout>
			<PagePending />
		</SpaceLayout>
	),
	errorComponent: (props) => (
		<SpaceLayout>
			<PageError {...props} />
		</SpaceLayout>
	),
	component: () => (
		<SpaceLayout>
			<Outlet />
		</SpaceLayout>
	),
});
