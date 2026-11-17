import { createFileRoute } from "@tanstack/react-router";

import { redirectIfLoggedIn } from "@/features/auth/auth-guard";
import { authSearchSchema } from "@/features/auth/auth-search";
import { LoginPage } from "@/features/auth/login-page";

export const Route = createFileRoute("/login")({
	validateSearch: authSearchSchema,
	beforeLoad: redirectIfLoggedIn,
	head: () => ({ meta: [{ title: "Connexion — Gaspirator" }] }),
	component: LoginRoute,
});

function LoginRoute() {
	const { role } = Route.useSearch();
	return <LoginPage role={role} />;
}
