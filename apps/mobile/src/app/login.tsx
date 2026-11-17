import { revalidateLogic, useForm } from "@tanstack/react-form";
import { useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";

import { AuthLayout } from "@/components/auth-layout";
import {
	BoundTextField,
	FormAlert,
	SubmitButton,
} from "@/components/form-controls";
import { Spacing } from "@/constants/theme";
import { login } from "@/features/auth/auth-api";
import { useAuthStore } from "@/features/auth/auth-store";
import { loginSchema } from "@/features/auth/login-schema";
import { errorMessage } from "@/lib/api-client";

// Same as the web: our own vague message on a 401, the API's precise one otherwise (403 pending…).
const LOGIN_ERRORS = {
	401: "E-mail ou mot de passe incorrect.",
};

export default function LoginScreen() {
	const router = useRouter();
	const setTokens = useAuthStore((state) => state.setTokens);
	const [error, setError] = useState<string | null>(null);

	const form = useForm({
		defaultValues: { email: "", password: "" },
		// Validate on submit first, then on every change so an error goes away as soon as it is fixed.
		validationLogic: revalidateLogic(),
		validators: { onDynamic: loginSchema },
		onSubmit: async ({ value }) => {
			setError(null);
			try {
				// Parse again so the submitted email is trimmed, as the schema defines.
				setTokens(await login(loginSchema.parse(value)));
			} catch (failure) {
				setError(errorMessage(failure, LOGIN_ERRORS));
				return;
			}
			router.replace("/");
		},
	});

	return (
		<AuthLayout
			eyebrow="Connexion"
			title="Se connecter"
			description="Retrouvez vos dons et vos réservations."
			footer={{
				text: "Pas encore de compte ?",
				linkLabel: "Créer un compte",
				href: "/register",
			}}
		>
			<View style={styles.form}>
				{error && <FormAlert>{error}</FormAlert>}

				<form.Field name="email">
					{(field) => (
						<BoundTextField
							field={field}
							label="E-mail"
							keyboardType="email-address"
							autoCapitalize="none"
							autoComplete="email"
							textContentType="emailAddress"
						/>
					)}
				</form.Field>
				<form.Field name="password">
					{(field) => (
						<BoundTextField
							field={field}
							label="Mot de passe"
							secureTextEntry
							autoComplete="current-password"
							textContentType="password"
							onSubmitEditing={form.handleSubmit}
						/>
					)}
				</form.Field>

				<form.Subscribe selector={(state) => state.isSubmitting}>
					{(isSubmitting) => (
						<SubmitButton
							pending={isSubmitting}
							pendingLabel="Connexion…"
							onPress={form.handleSubmit}
							label="Se connecter"
						/>
					)}
				</form.Subscribe>
			</View>
		</AuthLayout>
	);
}

const styles = StyleSheet.create({
	form: {
		gap: Spacing.three + Spacing.one,
	},
});
