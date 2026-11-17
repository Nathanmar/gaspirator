import { StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { SubmitButton } from "@/components/form-controls";
import { ThemedText } from "@/components/themed-text";
import { ThemedView } from "@/components/themed-view";
import { Spacing } from "@/constants/theme";
import { logout } from "@/features/auth/auth-api";
import { useAuthStore } from "@/features/auth/auth-store";
import { ApiError, NetworkError } from "@/lib/api-client";

export default function ProfileScreen() {
	const tokens = useAuthStore((state) => state.tokens);
	const me = useAuthStore((state) => state.me);
	const clearTokens = useAuthStore((state) => state.clearTokens);

	// Same as the web: the local session ends even if the server revocation fails.
	async function logOut() {
		if (tokens) {
			try {
				await logout(tokens);
			} catch (error) {
				if (!(error instanceof ApiError || error instanceof NetworkError))
					throw error;
			}
		}
		// The tabs layout then sends back to the welcome screen.
		clearTokens();
	}

	return (
		<ThemedView style={styles.container}>
			<SafeAreaView style={styles.content} edges={["top"]}>
				<View style={styles.identity}>
					<ThemedText accessibilityRole="header" style={styles.title}>
						Profil
					</ThemedText>
					{me && (
						<>
							<ThemedText>
								{me.firstname} {me.lastname}
							</ThemedText>
							<ThemedText themeColor="textSecondary">{me.email}</ThemedText>
						</>
					)}
				</View>
				<SubmitButton onPress={logOut} label="Se déconnecter" />
			</SafeAreaView>
		</ThemedView>
	);
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
	},
	content: {
		paddingHorizontal: Spacing.four,
		paddingTop: Spacing.four,
		gap: Spacing.four,
	},
	identity: {
		gap: Spacing.one,
	},
	title: {
		fontSize: 36,
		lineHeight: 40,
		fontWeight: 800,
		letterSpacing: -1.4,
	},
});
