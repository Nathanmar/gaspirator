import type { Me } from "./auth-api";
import { authorizedRequest } from "./authorized-request";

export function getMe(): Promise<Me> {
	return authorizedRequest<Me>("/me", { method: "GET" });
}

/** Where a user lands once logged in. Only the association space exists so far. */
export function homePath(me: Me): "/association" | "/" {
	return me.association ? "/association" : "/";
}
