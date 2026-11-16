import { useEffect, useRef, useState } from "react";

import { Link } from "@tanstack/react-router";

import { ArrowBadge, primaryButtonClass } from "@/components/form-controls";
import { errorMessage } from "@/lib/api-client";

import {
  type OrganizationType,
  type RegistrationRequest,
  type RegistrationRequestCreate,
  createRegistrationRequest,
} from "./auth-api";
import { AuthLayout } from "./auth-layout";
import { RegisterForm } from "./register-form";

// Our own texts for 409 and 422, independent of the server message (the mock server returns the
// same example body for every error).
const REGISTER_ERRORS = {
  409: "Un compte existe déjà avec cette adresse e-mail, ce SIRET ou ce n° RNA.",
  // The form already checks every format: a 422 mostly means the address was not found.
  422: "Certaines informations ont été refusées. Vérifiez notamment que l'adresse existe.",
};

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
      setError(errorMessage(failure, REGISTER_ERRORS));
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
            <ArrowBadge />
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
          <Link to="/login" search={{ role }}>
            Se connecter
          </Link>
        </>
      }
    >
      <RegisterForm defaultType={role} error={error} onSubmit={handleSubmit} />
    </AuthLayout>
  );
}
