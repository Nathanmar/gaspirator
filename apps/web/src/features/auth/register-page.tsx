import { useEffect, useRef, useState } from "react";

import { Link } from "@tanstack/react-router";

import { ArrowBadge, primaryButtonClass } from "@/components/form-controls";
import { errorMessage } from "@/lib/api-client";

import {
  type OrganizationType,
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

type SentRequest = { role: OrganizationType; name: string; email: string };

// The confirmation repeats what was sent rather than reading the response: the mock server answers
// every request with the same fixed example.
function summarize(payload: RegistrationRequestCreate): SentRequest {
  const role = "supplier" in payload ? "supplier" : "association";
  const organization = "supplier" in payload ? payload.supplier : payload.association;
  return { role, name: organization.name, email: payload.account.email };
}

export function RegisterPage({ role }: { role?: OrganizationType }) {
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState<SentRequest | null>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    // The confirmation replaces a long form: bring its title into view and announce it.
    if (sent) titleRef.current?.focus();
  }, [sent]);

  async function handleSubmit(payload: RegistrationRequestCreate) {
    setError(null);
    try {
      await createRegistrationRequest(payload);
      setSent(summarize(payload));
    } catch (failure) {
      setError(errorMessage(failure, REGISTER_ERRORS));
    }
  }

  if (sent) {
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
            <strong>{sent.name}</strong>. Vous pourrez vous connecter avec{" "}
            <strong>{sent.email}</strong> dès que la demande sera acceptée.
          </p>
          <Link
            to="/login"
            search={{ role: sent.role }}
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
