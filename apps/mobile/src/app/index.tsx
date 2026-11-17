import { Redirect, useRouter } from "expo-router";
import { Pressable, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { LogoMark } from "@/components/logo-mark";
import { ThemedText } from "@/components/themed-text";
import { ThemedView } from "@/components/themed-view";
import { Spacing } from "@/constants/theme";
import { useAuthHydrated, useAuthStore } from "@/features/auth/auth-store";
import { useTheme } from "@/hooks/use-theme";

// Shown only when nobody is logged in.
export default function WelcomeScreen() {
	const theme = useTheme();
	const router = useRouter();
	const hydrated = useAuthHydrated();
	const isLoggedIn = useAuthStore((state) => state.tokens !== null);

	const buttons = [
		{ href: "/login", label: "Connexion", color: theme.lime, outlined: false },
		{
			href: "/register",
			label: "Inscription",
			color: theme.tomato,
			outlined: true,
		},
	] as const;

	// The splash overlay covers this blank frame while the session is read back.
	if (!hydrated) return null;
	if (isLoggedIn) return <Redirect href="/dashboard" />;

	return (
		<ThemedView style={styles.container}>
			<SafeAreaView style={styles.safeArea}>
				<ThemedView style={styles.hero}>
					<LogoMark size={140} />
					<ThemedText style={styles.brand}>gaspirator</ThemedText>
				</ThemedView>

				{buttons.map((button) => (
					<Pressable
						key={button.href}
						accessibilityRole="button"
						onPress={() => router.push(button.href)}
						style={({ pressed }) => [
							styles.button,
							button.outlined
								? { borderWidth: 1.5, borderColor: button.color }
								: { backgroundColor: button.color },
							{ opacity: pressed ? 0.8 : 1 },
						]}
					>
						<ThemedText
							themeColor="onAccent"
							style={[
								styles.buttonLabel,
								button.outlined && { color: button.color },
							]}
						>
							{button.label}
						</ThemedText>
					</Pressable>
				))}
			</SafeAreaView>
		</ThemedView>
	);
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
	},
	safeArea: {
		flex: 1,
		paddingHorizontal: Spacing.four,
		paddingBottom: Spacing.four,
		gap: Spacing.three,
	},
	hero: {
		flex: 1,
		alignItems: "center",
		justifyContent: "center",
		gap: Spacing.three,
	},
	brand: {
		fontSize: 36,
		lineHeight: 40,
		fontWeight: 700,
		letterSpacing: -1,
	},
	// Same pill as the web primary button: rounded-full, h-14, uppercase, wide tracking.
	button: {
		height: 56,
		borderRadius: 999,
		alignItems: "center",
		justifyContent: "center",
	},
	buttonLabel: {
		fontSize: 13,
		fontWeight: 600,
		letterSpacing: 2.3,
		textTransform: "uppercase",
	},
});
