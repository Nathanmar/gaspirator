import { Redirect } from "expo-router";
import { NativeTabs } from "expo-router/native-tabs";
import { useEffect } from "react";

import { getMe } from "@/features/auth/auth-api";
import { useAuthHydrated, useAuthStore } from "@/features/auth/auth-store";
import { useTheme } from "@/hooks/use-theme";
import { ApiError } from "@/lib/api-client";

/**
 * Logged-in area: the native tab bar (Liquid Glass on iOS 26, Material on Android). Loads the
 * user once for every tab, and sends back to the welcome screen when the session is gone.
 */
export default function TabsLayout() {
	const theme = useTheme();
	const hydrated = useAuthHydrated();
	const accessToken = useAuthStore((state) => state.tokens?.access_token);
	const setMe = useAuthStore((state) => state.setMe);
	const clearTokens = useAuthStore((state) => state.clearTokens);

	useEffect(() => {
		if (!accessToken) return;
		getMe(accessToken)
			.then(setMe)
			.catch((error) => {
				// shortcut: an expired access token logs out; use POST /auth/refresh once sessions must last.
				if (error instanceof ApiError && error.status === 401) clearTokens();
			});
	}, [accessToken, setMe, clearTokens]);

	if (!hydrated) return null;
	if (!accessToken) return <Redirect href="/" />;

	return (
		<NativeTabs
			tintColor={theme.lime}
			backgroundColor={theme.background}
			indicatorColor={theme.backgroundSelected}
			labelStyle={{ selected: { color: theme.text } }}
		>
			<NativeTabs.Trigger name="dashboard">
				<NativeTabs.Trigger.Label>Accueil</NativeTabs.Trigger.Label>
				<NativeTabs.Trigger.Icon
					sf={{ default: "house", selected: "house.fill" }}
					md="home"
				/>
			</NativeTabs.Trigger>
			<NativeTabs.Trigger name="profile">
				<NativeTabs.Trigger.Label>Profil</NativeTabs.Trigger.Label>
				<NativeTabs.Trigger.Icon
					sf={{
						default: "person.crop.circle",
						selected: "person.crop.circle.fill",
					}}
					md="person"
				/>
			</NativeTabs.Trigger>
		</NativeTabs>
	);
}
