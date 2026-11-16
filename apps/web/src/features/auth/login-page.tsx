import { useState } from "react";

import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";

import { FormAlert } from "@/components/form-controls";
import { ApiError, NetworkError } from "@/lib/api-client";

import { type OrganizationType, login } from "./auth-api";
import { AuthLayout } from "./auth-layout";
import { useAuthStore } from "./auth-store";
import { LoginForm } from "./login-form";
import type { LoginFormValues } from "./login-schema";

const SPACE_BY_ROLE: Record<OrganizationType, string> = {
  supplier: "Espace fournisseur",
  association: "Espace association",
};

/**
 * Message shown for a failed login. 401 and 403 get our own text: the contract makes the 401
 * message deliberately vague, and the mock server returns the same example body for every error.
 */
function loginErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return "E-mail ou mot de passe incorrect.";
    if (error.status === 403) {
      return "Votre compte n'est pas encore actif : votre demande d'inscription est en attente de validation ou a été refusée.";
    }
    return error.message;
  }
  if (error instanceof NetworkError) return error.message;
  // Anything else is a bug: let it surface instead of hiding it behind a message.
  throw error;
}

export function LoginPage({ role }: { role?: OrganizationType }) {
  const navigate = useNavigate();
  const setTokens = useAuthStore((state) => state.setTokens);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(credentials: LoginFormValues) {
    setError(null);
    try {
      setTokens(await login(credentials));
    } catch (failure) {
      setError(loginErrorMessage(failure));
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
    >
      <div className="flex flex-col gap-5">
        {error && <FormAlert>{error}</FormAlert>}
        <LoginForm onSubmit={handleSubmit} />
      </div>
    </AuthLayout>
  );
}
