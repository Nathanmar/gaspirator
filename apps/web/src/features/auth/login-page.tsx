import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";

import { FormAlert } from "@/components/form-controls";
import { ApiError, errorMessage, NetworkError } from "@/lib/api-client";

import { login, type OrganizationType } from "./auth-api";
import { AuthLayout } from "./auth-layout";
import { useAuthStore } from "./auth-store";
import { LoginForm } from "./login-form";
import type { LoginFormValues } from "./login-schema";
import { getMe, homePath } from "./me";

const SPACE_BY_ROLE: Record<OrganizationType, string> = {
	supplier: "Espace fournisseur",
	association: "Espace association",
};

// The contract keeps the 401 message deliberately vague: we always show our own. Other errors (403
// pending or rejected registration…) show the API's message, which is precise.
const LOGIN_ERRORS = {
	401: "E-mail ou mot de passe incorrect.",
};

// The user is logged in even if the profile fails to load: the home page will do.
async function landingPath() {
	try {
		return homePath(await getMe());
	} catch (error) {
		if (error instanceof ApiError || error instanceof NetworkError) return "/";
		throw error;
	}
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
			setError(errorMessage(failure, LOGIN_ERRORS));
			return;
		}
		toast.success("Vous êtes connecté.");
		await navigate({ to: await landingPath() });
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
