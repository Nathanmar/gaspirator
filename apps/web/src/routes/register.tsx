import { createFileRoute } from "@tanstack/react-router";

import { redirectIfLoggedIn } from "@/features/auth/auth-guard";
import { authSearchSchema } from "@/features/auth/auth-search";
import { RegisterPage } from "@/features/auth/register-page";

export const Route = createFileRoute("/register")({
  validateSearch: authSearchSchema,
  beforeLoad: redirectIfLoggedIn,
  head: () => ({ meta: [{ title: "Inscription — Gaspirator" }] }),
  component: RegisterRoute,
});

function RegisterRoute() {
  const { role } = Route.useSearch();
  return <RegisterPage role={role} />;
}
