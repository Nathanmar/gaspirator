import { useState } from "react";

import { Link, useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";

import { FormAlert } from "@/components/form-controls";
import { errorMessage } from "@/lib/api-client";

import { type OrganizationType, login } from "./auth-api";
import { AuthLayout } from "./auth-layout";
import { useAuthStore } from "./auth-store";
import { LoginForm } from "./login-form";
import type { LoginFormValues } from "./login-schema";

const SPACE_BY_ROLE: Record<OrganizationType, string> = {
  supplier: "Espace fournisseur",
  association: "Espace association",
};

// Our own texts for 401 and 403: the contract makes the 401 message deliberately vague, and the mock
// server returns the same example body for every error.
const LOGIN_ERRORS = {
  401: "E-mail ou mot de passe incorrect.",
  403: "Votre compte n'est pas encore actif : votre demande d'inscription est en attente de validation ou a été refusée.",
};

export function LoginPage({ role }: { role?: OrganizationType }) {
  const navigate = useNavigate();
  const setTokens = useAuthStore((state) => state.setTokens);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(credentials: LoginFormValues) {
    setError(null);
    try {
      setTokens(await login(credentials));
    } catch (failure) {
      setError(errorMessage(failure, LOGIN_ERRORS));
      return;
    }
    toast.success("Vous êtes connecté.");
    await navigate({ to: "/" });
  }

  return (
    <AuthLayout
      eyebrow={role ? SPACE_BY_ROLE[role] : "Connexion"}
      title="Se connecter"
      description="Retrouvez vos dons et vos réservations."
      footer={
        <>
          Pas encore de compte ?{" "}
          <Link to="/register" search={{ role }}>
            Créer un compte
          </Link>
        </>
      }
    >
      <div className="flex flex-col gap-5">
        {error && <FormAlert>{error}</FormAlert>}
        <LoginForm onSubmit={handleSubmit} />
      </div>
    </AuthLayout>
  );
}
