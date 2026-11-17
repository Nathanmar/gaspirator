import type { AnyFieldApi } from "@tanstack/react-form";
import type { ReactNode } from "react";
import {
	ActivityIndicator,
	Pressable,
	StyleSheet,
	TextInput,
	type TextInputProps,
	View,
} from "react-native";

import { ThemedText } from "@/components/themed-text";
import { Spacing } from "@/constants/theme";
import { useTheme } from "@/hooks/use-theme";

// Native counterparts of apps/web form-controls: 48px touch targets and a 16px font size.

/** First validation error of a TanStack Form field, as shown under its control. */
export function firstError(field: AnyFieldApi): string | undefined {
	return field.state.meta.errors[0]?.message;
}

function Label({ children }: { children: string }) {
	return (
		<ThemedText themeColor="textSecondary" style={styles.label}>
			{children}
		</ThemedText>
	);
}

function FieldError({ error }: { error?: string }) {
	const theme = useTheme();
	if (!error) return null;
	return (
		<ThemedText
			accessibilityLiveRegion="polite"
			style={[styles.error, { color: theme.tomato }]}
		>
			{error}
		</ThemedText>
	);
}

type BoundTextFieldProps = { field: AnyFieldApi; label: string } & Omit<
	TextInputProps,
	"value" | "onChangeText" | "onBlur"
>;

/** Text input bound to a TanStack Form field: value, change, blur and error. */
export function BoundTextField({
	field,
	label,
	...props
}: BoundTextFieldProps) {
	const theme = useTheme();
	const error = firstError(field);

	return (
		<View style={styles.field}>
			<Label>{label}</Label>
			<TextInput
				accessibilityLabel={label}
				value={field.state.value}
				onChangeText={field.handleChange}
				onBlur={field.handleBlur}
				placeholderTextColor={theme.textSecondary}
				style={[
					styles.input,
					{
						color: theme.text,
						backgroundColor: theme.backgroundElement,
						borderColor: error ? theme.tomato : theme.backgroundSelected,
					},
				]}
				{...props}
			/>
			<FieldError error={error} />
		</View>
	);
}

type Option<T extends string> = { value: T; label: string };

/** Radio group shown as pills; the checked one is filled with lime. */
export function ChoiceField<T extends string>({
	legend,
	options,
	value,
	onChange,
	error,
}: {
	legend: string;
	options: readonly Option<T>[];
	value: string;
	onChange: (value: T) => void;
	error?: string;
}) {
	const theme = useTheme();

	return (
		<View style={styles.field} accessibilityRole="radiogroup">
			<Label>{legend}</Label>
			<View style={styles.choices}>
				{options.map((option) => {
					const checked = value === option.value;
					return (
						<Pressable
							key={option.value}
							accessibilityRole="radio"
							accessibilityState={{ checked }}
							onPress={() => onChange(option.value)}
							style={[
								styles.choice,
								checked
									? { backgroundColor: theme.lime, borderColor: theme.lime }
									: {
											backgroundColor: theme.backgroundElement,
											borderColor: theme.backgroundSelected,
										},
							]}
						>
							<ThemedText
								themeColor={checked ? "onAccent" : "text"}
								style={styles.choiceLabel}
							>
								{option.label}
							</ThemedText>
						</Pressable>
					);
				})}
			</View>
			<FieldError error={error} />
		</View>
	);
}

/** Main call to action: lime pill, like the welcome screen's "Connexion". */
export function SubmitButton({
	pending = false,
	pendingLabel,
	onPress,
	label,
}: {
	pending?: boolean;
	// Replaces the label while the request is running, e.g. "Connexion…".
	pendingLabel?: string;
	onPress: () => void;
	label: string;
}) {
	const theme = useTheme();

	return (
		<Pressable
			accessibilityRole="button"
			accessibilityState={{ busy: pending, disabled: pending }}
			disabled={pending}
			onPress={onPress}
			style={({ pressed }) => [
				styles.button,
				{ backgroundColor: theme.lime, opacity: pending || pressed ? 0.8 : 1 },
			]}
		>
			{pending && <ActivityIndicator color={theme.onAccent} />}
			<ThemedText themeColor="onAccent" style={styles.buttonLabel}>
				{pending && pendingLabel ? pendingLabel : label}
			</ThemedText>
		</Pressable>
	);
}

/** Error of the whole form (wrong credentials, server unreachable…), announced when it appears. */
export function FormAlert({ children }: { children: ReactNode }) {
	const theme = useTheme();

	return (
		<View
			accessibilityRole="alert"
			accessibilityLiveRegion="assertive"
			style={[styles.alert, { borderColor: theme.tomato }]}
		>
			{typeof children === "string" ? (
				<ThemedText type="small">{children}</ThemedText>
			) : (
				children
			)}
		</View>
	);
}

const styles = StyleSheet.create({
	field: {
		gap: Spacing.two,
	},
	label: {
		fontSize: 12,
		lineHeight: 16,
		fontWeight: 600,
		letterSpacing: 1.7,
		textTransform: "uppercase",
	},
	input: {
		height: 48,
		borderWidth: 1,
		borderRadius: 16,
		paddingHorizontal: Spacing.three,
		fontSize: 16,
	},
	error: {
		fontSize: 14,
		lineHeight: 20,
	},
	choices: {
		flexDirection: "row",
		flexWrap: "wrap",
		gap: Spacing.two,
	},
	choice: {
		flexGrow: 1,
		flexBasis: "40%",
		height: 48,
		borderWidth: 1,
		borderRadius: 999,
		alignItems: "center",
		justifyContent: "center",
	},
	choiceLabel: {
		fontSize: 14,
		fontWeight: 600,
	},
	button: {
		height: 56,
		borderRadius: 999,
		flexDirection: "row",
		gap: Spacing.two,
		alignItems: "center",
		justifyContent: "center",
	},
	buttonLabel: {
		fontSize: 13,
		fontWeight: 600,
		letterSpacing: 2.3,
		textTransform: "uppercase",
	},
	alert: {
		borderWidth: 1,
		borderRadius: 16,
		paddingHorizontal: Spacing.three,
		paddingVertical: Spacing.two + Spacing.one,
		gap: Spacing.one,
	},
});
