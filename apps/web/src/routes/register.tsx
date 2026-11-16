import { createFileRoute } from "@tanstack/react-router";

import { authSearchSchema } from "@/features/auth/auth-search";
import { RegisterPage } from "@/features/auth/register-page";

export const Route = createFileRoute("/register")({
  validateSearch: authSearchSchema,
  head: () => ({ meta: [{ title: "Inscription — Gaspirator" }] }),
  component: RegisterRoute,
});

function RegisterRoute() {
  const { role } = Route.useSearch();
  return <RegisterPage role={role} />;
}
