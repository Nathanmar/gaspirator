import { redirect } from "@tanstack/react-router";

import { useAuthStore } from "./auth-store";

/** `beforeLoad` of the login and registration routes: a logged-in user goes to the home page. */
export function redirectIfLoggedIn() {
	if (useAuthStore.getState().tokens) throw redirect({ to: "/" });
}
