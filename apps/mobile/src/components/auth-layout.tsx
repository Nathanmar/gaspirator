import { Link, type LinkProps } from "expo-router";
import type { ReactNode } from "react";
import {
	KeyboardAvoidingView,
	Platform,
	ScrollView,
	StyleSheet,
	View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { LogoMark } from "@/components/logo-mark";
import { ThemedText } from "@/components/themed-text";
import { ThemedView } from "@/components/themed-view";
import { Spacing } from "@/constants/theme";
import { useTheme } from "@/hooks/use-theme";

type AuthLayoutProps = {
	// Small lime line above the title, as on the web auth pages.
	eyebrow: string;
	title: string;
	description?: string;
	// Under the form: link to the other auth screen.
	footer?: { text: string; linkLabel: string; href: LinkProps["href"] };
	children: ReactNode;
};

/** Shell of the login and registration screens, mirroring apps/web AuthLayout. */
export function AuthLayout({
	eyebrow,
	title,
	description,
	footer,
	children,
}: AuthLayoutProps) {
	const theme = useTheme();

	return (
		<ThemedView style={styles.container}>
			<SafeAreaView style={styles.container}>
				<KeyboardAvoidingView
					style={styles.container}
					behavior={Platform.OS === "ios" ? "padding" : undefined}
				>
					<ScrollView
						contentContainerStyle={styles.content}
						keyboardShouldPersistTaps="handled"
					>
						<Link href="/" accessibilityLabel="Gaspirator, retour à l'accueil">
							<LogoMark size={36} />
						</Link>

						<View style={styles.intro}>
							<ThemedText style={[styles.eyebrow, { color: theme.lime }]}>
								{eyebrow}
							</ThemedText>
							<ThemedText accessibilityRole="header" style={styles.title}>
								{title}
							</ThemedText>
							{description && (
								<ThemedText themeColor="textSecondary">
									{description}
								</ThemedText>
							)}
						</View>

						{children}

						{footer && (
							<ThemedText
								type="small"
								themeColor="textSecondary"
								style={styles.footer}
							>
								{footer.text}{" "}
								<Link href={footer.href} replace>
									<ThemedText type="smallBold" style={styles.footerLink}>
										{footer.linkLabel}
									</ThemedText>
								</Link>
							</ThemedText>
						)}
					</ScrollView>
				</KeyboardAvoidingView>
			</SafeAreaView>
		</ThemedView>
	);
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
	},
	content: {
		flexGrow: 1,
		paddingHorizontal: Spacing.four,
		paddingVertical: Spacing.three,
		gap: Spacing.four,
	},
	intro: {
		gap: Spacing.two,
	},
	eyebrow: {
		fontSize: 14,
		fontWeight: 600,
		letterSpacing: 1.7,
		textTransform: "uppercase",
	},
	title: {
		fontSize: 40,
		lineHeight: 42,
		fontWeight: 800,
		letterSpacing: -1.6,
	},
	footer: {
		textAlign: "center",
	},
	footerLink: {
		textDecorationLine: "underline",
	},
});
