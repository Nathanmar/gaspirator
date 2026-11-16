import { useEffect, useRef, useState } from "react";

import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";

import { primaryButtonClass } from "@/components/form-controls";
import { ApiError, NetworkError } from "@/lib/api-client";

import {
  type OrganizationType,
  type RegistrationRequest,
  type RegistrationRequestCreate,
  createRegistrationRequest,
} from "./auth-api";
import { AuthLayout } from "./auth-layout";
import { RegisterForm } from "./register-form";

/**
 * Message shown for a failed registration. 409 and 422 get our own text, which does not depend on
 * the server message (the mock server returns the same example body for every error).
 */
function registerErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 409) {
      return "Un compte existe déjà avec cette adresse e-mail, ce SIRET ou ce n° RNA.";
    }
    if (error.status === 422) {
      // The form already checks every format: a 422 mostly means the address was not found.
      return "Certaines informations ont été refusées. Vérifiez notamment que l'adresse existe.";
    }
    return error.message;
  }
  if (error instanceof NetworkError) return error.message;
  // Anything else is a bug: let it surface instead of hiding it behind a message.
  throw error;
}

const linkClass = "font-semibold text-cream underline underline-offset-4";

export function RegisterPage({ role }: { role?: OrganizationType }) {
  const [error, setError] = useState<string | null>(null);
  const [request, setRequest] = useState<RegistrationRequest | null>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    // The confirmation replaces a long form: bring its title into view and announce it.
    if (request) titleRef.current?.focus();
  }, [request]);

  async function handleSubmit(payload: RegistrationRequestCreate) {
    setError(null);
    try {
      setRequest(await createRegistrationRequest(payload));
    } catch (failure) {
      setError(registerErrorMessage(failure));
    }
  }

  if (request) {
    return (
      <AuthLayout
        eyebrow="Inscription"
        title="Demande envoyée"
        titleRef={titleRef}
        description="Merci ! Votre demande est en attente de validation."
      >
        <div className="flex flex-col gap-6">
          <p className="leading-snug">
            Un administrateur va vérifier les informations de{" "}
            <strong>{request.organization.name}</strong>. Vous pourrez vous connecter avec{" "}
            <strong>{request.account.email}</strong> dès que la demande sera acceptée.
          </p>
          <Link
            to="/login"
            search={{ role: request.organization.type }}
            className={primaryButtonClass}
          >
            Aller à la connexion
            <span
              aria-hidden="true"
              className="grid size-10 place-items-center rounded-full bg-ink text-cream transition-transform duration-300 group-hover:rotate-45"
            >
              <ArrowUpRight className="size-4" />
            </span>
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      wide
      eyebrow="Inscription"
      title="Rejoindre Gaspirator"
      description="Créez l'espace de votre organisation. Un administrateur validera votre demande avant votre première connexion."
      footer={
        <>
          Déjà un compte ?{" "}
          <Link to="/login" search={{ role }} className={linkClass}>
            Se connecter
          </Link>
        </>
      }
    >
      <RegisterForm defaultType={role} error={error} onSubmit={handleSubmit} />
    </AuthLayout>
  );
}
