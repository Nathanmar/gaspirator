import { env } from "@gaspirator/env/native";
import Constants from "expo-constants";

/**
 * API base URL. On a phone, "localhost" is the phone itself: in development the loopback host is
 * swapped for the computer running Metro (`hostUri`, e.g. "10.70.1.148:8081"), so the same .env
 * works on the simulator, a real device and any Wi-Fi network.
 */
export function apiBaseUrl(
	configured = env.EXPO_PUBLIC_API_URL,
	hostUri = Constants.expoConfig?.hostUri,
): string {
	const url = new URL(configured);
	const devHost = hostUri?.split(":")[0];
	if (devHost && ["127.0.0.1", "localhost"].includes(url.hostname)) {
		url.hostname = devHost;
	}
	return url.toString().replace(/\/$/, "");
}
