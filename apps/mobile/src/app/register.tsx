import { revalidateLogic, useForm, useStore } from "@tanstack/react-form";
import { useRouter } from "expo-router";
import { type ReactNode, useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import { AuthLayout } from "@/components/auth-layout";
import {
	BoundTextField,
	ChoiceField,
	FormAlert,
	firstError,
	SubmitButton,
} from "@/components/form-controls";
import { ThemedText } from "@/components/themed-text";
import { Spacing } from "@/constants/theme";
import {
	createRegistrationRequest,
	type OrganizationType,
	type RegistrationRequestCreate,
	type SupplierType,
} from "@/features/auth/auth-api";
import {
	accountSchema,
	organizationSchema,
	type RegisterFormValues,
	registerSchema,
	SUPPLIER_TYPES,
} from "@/features/auth/register-schema";
import { useTheme } from "@/hooks/use-theme";
import { ApiError, errorMessage } from "@/lib/api-client";

type AccountValues = RegisterFormValues["account"];
type OrganizationValues = RegisterFormValues["organization"];

const ORGANIZATION_TYPES = [
	{ value: "supplier", label: "Fournisseur" },
	{ value: "association", label: "Association" },
] as const;

const SUPPLIER_TYPE_LABELS: Record<SupplierType, string> = {
	canteen: "Cantine",
	hospital: "Hôpital",
	supermarket: "Supermarché",
	other: "Autre",
};

const SUPPLIER_TYPE_OPTIONS = SUPPLIER_TYPES.map((value) => ({
	value,
	label: SUPPLIER_TYPE_LABELS[value],
}));

const LEGAL_ID_LABELS: Record<OrganizationType | "", string> = {
	supplier: "SIRET",
	association: "N° RNA",
	"": "SIRET ou n° RNA",
};

// Field paths of a 422, as labelled in the form; shared supplier/association fields have no prefix.
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

/** Same rules as the web: API messages as is, and the refused fields listed on a 422. */
function registerError(failure: unknown): ReactNode {
	if (
		failure instanceof ApiError &&
		failure.status === 422 &&
		failure.details.length > 0
	) {
		return (
			<>
				<ThemedText type="small">
					Certaines informations ont été refusées&nbsp;:
				</ThemedText>
				{failure.details.map((detail) => (
					<ThemedText key={`${detail.field}-${detail.message}`} type="small">
						• {fieldLabel(detail.field)}&nbsp;: {detail.message}
					</ThemedText>
				))}
			</>
		);
	}
	return errorMessage(failure, {
		422: "Certaines informations ont été refusées. Vérifiez le formulaire.",
	});
}

const EMPTY_VALUES: RegisterFormValues = {
	account: {
		firstname: "",
		lastname: "",
		email: "",
		password: "",
		password_confirmation: "",
	},
	organization: {
		type: "",
		name: "",
		legal_id: "",
		supplier_type: "",
		contact_phone: "",
	},
};

/** Progress bar, step number and title of a step. */
function StepHeader({ step, title }: { step: 1 | 2; title: string }) {
	const theme = useTheme();

	return (
		<View style={styles.stepHeader}>
			<View style={styles.progress}>
				<View style={[styles.progressBar, { backgroundColor: theme.lime }]} />
				<View
					style={[
						styles.progressBar,
						{
							backgroundColor:
								step === 2 ? theme.lime : theme.backgroundSelected,
						},
					]}
				/>
			</View>
			<ThemedText type="small" themeColor="textSecondary">
				{`Étape ${step} sur 2`}
			</ThemedText>
			<ThemedText accessibilityRole="header" style={styles.stepTitle}>
				{title}
			</ThemedText>
		</View>
	);
}

/** Step 1: the account of the organization's manager. */
function AccountStep({
	defaultValues,
	onContinue,
}: {
	defaultValues: AccountValues;
	onContinue: (account: AccountValues) => void;
}) {
	const form = useForm({
		defaultValues,
		validationLogic: revalidateLogic(),
		validators: { onDynamic: accountSchema },
		// Raw values are kept (not the parsed ones) so they show unchanged when coming back.
		onSubmit: ({ value }) => onContinue(value),
	});

	return (
		<View style={styles.form}>
			<StepHeader step={1} title="Votre compte" />

			<form.Field name="firstname">
				{(field) => (
					<BoundTextField
						field={field}
						label="Prénom"
						autoComplete="given-name"
						textContentType="givenName"
					/>
				)}
			</form.Field>
			<form.Field name="lastname">
				{(field) => (
					<BoundTextField
						field={field}
						label="Nom"
						autoComplete="family-name"
						textContentType="familyName"
					/>
				)}
			</form.Field>
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
						autoComplete="new-password"
						textContentType="newPassword"
					/>
				)}
			</form.Field>
			<form.Field name="password_confirmation">
				{(field) => (
					<BoundTextField
						field={field}
						label="Confirmation du mot de passe"
						secureTextEntry
						autoComplete="new-password"
						textContentType="newPassword"
					/>
				)}
			</form.Field>

			<SubmitButton onPress={form.handleSubmit} label="Continuer" />
		</View>
	);
}

/** Step 2: the organization, then the request is sent. */
function OrganizationStep({
	defaultValues,
	error,
	onBack,
	onSubmit,
}: {
	defaultValues: OrganizationValues;
	error: ReactNode;
	// Receives the current values so they are kept when coming back to this step.
	onBack: (organization: OrganizationValues) => void;
	onSubmit: (organization: OrganizationValues) => Promise<void>;
}) {
	const form = useForm({
		defaultValues,
		validationLogic: revalidateLogic(),
		validators: { onDynamic: organizationSchema },
		onSubmit: ({ value }) => onSubmit(value),
	});
	// The legal ID label and the establishment type depend on the organization type.
	const type = useStore(form.store, (state) => state.values.type);

	return (
		<View style={styles.form}>
			<StepHeader step={2} title="Votre organisation" />

			<form.Field name="type">
				{(field) => (
					<ChoiceField
						legend="Type d'organisation"
						options={ORGANIZATION_TYPES}
						value={field.state.value}
						onChange={field.handleChange}
						error={firstError(field)}
					/>
				)}
			</form.Field>
			<form.Field name="name">
				{(field) => (
					<BoundTextField
						field={field}
						label="Nom de l'organisation"
						textContentType="organizationName"
					/>
				)}
			</form.Field>
			<form.Field name="legal_id">
				{(field) => (
					<BoundTextField
						field={field}
						label={LEGAL_ID_LABELS[type]}
						autoCapitalize="characters"
						autoCorrect={false}
						// A SIRET is only digits: show the numeric keypad.
						keyboardType={type === "supplier" ? "number-pad" : "default"}
						placeholder={type === "association" ? "W123456789" : undefined}
					/>
				)}
			</form.Field>
			{type === "supplier" && (
				<form.Field name="supplier_type">
					{(field) => (
						<ChoiceField
							legend="Type d'établissement"
							options={SUPPLIER_TYPE_OPTIONS}
							value={field.state.value}
							onChange={field.handleChange}
							error={firstError(field)}
						/>
					)}
				</form.Field>
			)}
			<form.Field name="contact_phone">
				{(field) => (
					<BoundTextField
						field={field}
						label="Téléphone"
						keyboardType="phone-pad"
						autoComplete="tel"
						textContentType="telephoneNumber"
					/>
				)}
			</form.Field>

			{/* The error sits next to the submit button, where the user is looking. */}
			{error && <FormAlert>{error}</FormAlert>}
			<form.Subscribe selector={(state) => state.isSubmitting}>
				{(isSubmitting) => (
					<>
						<SubmitButton
							pending={isSubmitting}
							pendingLabel="Envoi…"
							onPress={form.handleSubmit}
							label="Envoyer ma demande"
						/>
						<Pressable
							accessibilityRole="button"
							disabled={isSubmitting}
							onPress={() => onBack(form.state.values)}
							style={styles.back}
						>
							<ThemedText type="smallBold" themeColor="textSecondary">
								← Retour
							</ThemedText>
						</Pressable>
					</>
				)}
			</form.Subscribe>
		</View>
	);
}

type SentRequest = { name: string; email: string };

// The confirmation repeats what was sent: the Prism mock answers every request with the same example.
function summarize(payload: RegistrationRequestCreate): SentRequest {
	const organization =
		"supplier" in payload ? payload.supplier : payload.association;
	return { name: organization.name, email: payload.account.email };
}

/**
 * Registration in two steps: the manager's account, then the organization. The values of both
 * steps live here, so going back and forth loses nothing.
 */
export default function RegisterScreen() {
	const router = useRouter();
	const [values, setValues] = useState(EMPTY_VALUES);
	const [step, setStep] = useState<"account" | "organization">("account");
	const [error, setError] = useState<ReactNode>(null);
	const [sent, setSent] = useState<SentRequest | null>(null);

	async function handleSubmit(organization: OrganizationValues) {
		setError(null);
		// The full schema output is the request body of the contract (without the confirmation).
		const payload = registerSchema.parse({ ...values, organization });
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
				eyebrow="Inscription"
				title="Demande envoyée"
				description="Merci ! Votre demande est en attente de validation."
			>
				<View style={styles.form}>
					<ThemedText>
						Un administrateur va vérifier les informations de{" "}
						<ThemedText type="smallBold" style={styles.strong}>
							{sent.name}
						</ThemedText>
						. Vous pourrez vous connecter avec{" "}
						<ThemedText type="smallBold" style={styles.strong}>
							{sent.email}
						</ThemedText>{" "}
						dès que la demande sera acceptée.
					</ThemedText>
					<SubmitButton
						onPress={() => router.replace("/login")}
						label="Aller à la connexion"
					/>
				</View>
			</AuthLayout>
		);
	}

	return (
		<AuthLayout
			eyebrow="Inscription"
			title="Rejoindre Gaspirator"
			description="Créez l'espace de votre organisation. Un administrateur validera votre demande avant votre première connexion."
			footer={{
				text: "Déjà un compte ?",
				linkLabel: "Se connecter",
				href: "/login",
			}}
		>
			{step === "account" ? (
				<AccountStep
					defaultValues={values.account}
					onContinue={(account) => {
						setValues({ ...values, account });
						setStep("organization");
					}}
				/>
			) : (
				<OrganizationStep
					defaultValues={values.organization}
					error={error}
					onBack={(organization) => {
						setValues({ ...values, organization });
						setStep("account");
					}}
					onSubmit={handleSubmit}
				/>
			)}
		</AuthLayout>
	);
}

const styles = StyleSheet.create({
	form: {
		gap: Spacing.three + Spacing.one,
	},
	stepHeader: {
		gap: Spacing.two,
	},
	progress: {
		flexDirection: "row",
		gap: Spacing.two,
	},
	progressBar: {
		flex: 1,
		height: 4,
		borderRadius: 999,
	},
	stepTitle: {
		fontSize: 24,
		lineHeight: 28,
		fontWeight: 800,
		letterSpacing: -0.7,
	},
	back: {
		height: 48,
		alignSelf: "center",
		justifyContent: "center",
		paddingHorizontal: Spacing.four,
	},
	strong: {
		fontSize: 16,
	},
});
