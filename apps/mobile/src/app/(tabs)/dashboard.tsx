import { ActivityIndicator, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { ThemedText } from "@/components/themed-text";
import { ThemedView } from "@/components/themed-view";
import { Spacing } from "@/constants/theme";
import { useAuthStore } from "@/features/auth/auth-store";
import { useTheme } from "@/hooks/use-theme";

export default function DashboardScreen() {
	const theme = useTheme();
	const me = useAuthStore((state) => state.me);

	return (
		<ThemedView style={styles.container}>
			<SafeAreaView style={styles.content} edges={["top"]}>
				<ThemedText style={[styles.eyebrow, { color: theme.lime }]}>
					Tableau de bord
				</ThemedText>
				{me ? (
					<ThemedText accessibilityRole="header" style={styles.title}>
						Bonjour, {me.firstname} {me.lastname}
					</ThemedText>
				) : (
					<ActivityIndicator color={theme.lime} style={styles.loader} />
				)}
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
		gap: Spacing.two,
	},
	eyebrow: {
		fontSize: 14,
		fontWeight: 600,
		letterSpacing: 1.7,
		textTransform: "uppercase",
	},
	title: {
		fontSize: 36,
		lineHeight: 40,
		fontWeight: 800,
		letterSpacing: -1.4,
	},
	loader: {
		alignSelf: "flex-start",
		marginTop: Spacing.three,
	},
});
