import { redirect } from "@tanstack/react-router";

import type { OrganizationType } from "./auth-api";
import { useAuthStore } from "./auth-store";

/** `beforeLoad` of the pages of a space: a visitor goes to the login page of that space. */
export function requireLogin(role: OrganizationType) {
	if (!useAuthStore.getState().tokens) {
		throw redirect({ to: "/login", search: { role } });
	}
}

/** `beforeLoad` of the login and registration routes: a logged-in user goes to the home page. */
export function redirectIfLoggedIn() {
	if (useAuthStore.getState().tokens) throw redirect({ to: "/" });
}
