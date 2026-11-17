import { Link } from "@tanstack/react-router";
import { type ReactNode, useEffect, useRef, useState } from "react";

import { ArrowBadge, primaryButtonClass } from "@/components/form-controls";
import { ApiError, errorMessage } from "@/lib/api-client";

import {
	createRegistrationRequest,
	type OrganizationType,
	type RegistrationRequestCreate,
} from "./auth-api";
import { AuthLayout } from "./auth-layout";
import { RegisterForm } from "./register-form";

// Field paths of a 422 (`account.email`, `supplier.contact_phone`…), as labelled in the form. The
// fields shared by suppliers and associations are listed without their prefix.
const FIELD_LABELS: Record<string, string> = {
	"account.firstname": "Prénom",
	"account.lastname": "Nom",
	"account.email": "E-mail",
	"account.password": "Mot de passe",
	"supplier.legal_id": "SIRET",
	"association.legal_id": "N° RNA",
	"supplier.supplier_type": "Type d'établissement",
	name: "Nom de l'organisation",
	contact_phone: "Téléphone",
};

function fieldLabel(field: string): string {
	const shared = field.replace(/^(supplier|association)\./, "");
	return FIELD_LABELS[field] ?? FIELD_LABELS[shared] ?? field;
}

/**
 * Error shown for a failed registration. The API's messages are shown as is (409 tells whether
 * the e-mail or the SIRET / RNA number is already used); a 422 lists the refused fields, which the
 * form could not catch itself (e.g. an e-mail domain or a phone number the server rejects).
 */
function registerError(failure: unknown): ReactNode {
	if (
		failure instanceof ApiError &&
		failure.status === 422 &&
		failure.details.length > 0
	) {
		return (
			<>
				{/* Non-breaking spaces before the colons, as French typography wants. */}
				Certaines informations ont été refusées&nbsp;:
				<ul className="mt-1 list-disc pl-5">
					{failure.details.map((detail) => (
						<li key={`${detail.field}-${detail.message}`}>
							{fieldLabel(detail.field)}&nbsp;: {detail.message}
						</li>
					))}
				</ul>
			</>
		);
	}
	return errorMessage(failure, {
		422: "Certaines informations ont été refusées. Vérifiez le formulaire.",
	});
}

type SentRequest = { role: OrganizationType; name: string; email: string };

// The confirmation repeats what was sent rather than reading the response: the Prism mock answers
// every request with the same fixed example.
function summarize(payload: RegistrationRequestCreate): SentRequest {
	const role = "supplier" in payload ? "supplier" : "association";
	const organization =
		"supplier" in payload ? payload.supplier : payload.association;
	return { role, name: organization.name, email: payload.account.email };
}

export function RegisterPage({ role }: { role?: OrganizationType }) {
	const [error, setError] = useState<ReactNode>(null);
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
			setError(registerError(failure));
		}
	}

	if (sent) {
		return (
			<AuthLayout
				centered
				mark={
					<div aria-hidden="true" className="relative mx-auto mb-6 size-16">
						<span className="success-ring absolute inset-0 rounded-full border-2 border-lime opacity-0" />
						<svg
							aria-hidden="true"
							viewBox="0 0 24 24"
							className="success-pop size-16 rounded-full bg-lime p-4 text-ink"
						>
							<path
								className="success-check"
								d="M5 12.5l4.5 4.5L19 7.5"
								pathLength={1}
								fill="none"
								stroke="currentColor"
								strokeWidth={3}
								strokeLinecap="round"
								strokeLinejoin="round"
							/>
						</svg>
					</div>
				}
				eyebrow="Inscription"
				title="Demande envoyée"
				titleRef={titleRef}
				description="Merci ! Votre demande est en attente de validation."
			>
				<div className="flex flex-col gap-6">
					<p className="leading-snug wrap-anywhere">
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
