import { apiRequest } from "@/lib/api-client";

/**
 * Whether a user registers (or manages) a supplier or an association. Front-only: the contract has
 * one schema per kind, e.g. `SupplierCreate` and `AssociationCreate`.
 */
export type OrganizationType = "supplier" | "association";

/** `SupplierType` in the API contract: kind of establishment of a supplier. */
export type SupplierType = "canteen" | "hospital" | "supermarket" | "other";

type Address = { street: string; postal_code: string; city: string };

/** `SupplierCreate` in the API contract. */
export type SupplierCreate = {
	name: string;
	// SIRET: 14 digits.
	legal_id: string;
	supplier_type: SupplierType;
	address: Address;
	contact_phone: string;
};

/** `AssociationCreate` in the API contract. */
export type AssociationCreate = {
	name: string;
	// RNA number: W followed by 9 digits.
	legal_id: string;
	address: Address;
	contact_phone: string;
};

/** `AccountCreate` in the API contract: the manager's account. */
type AccountCreate = {
	firstname: string;
	lastname: string;
	email: string;
	password: string;
};

/** `RegistrationRequestCreate` in the API contract: a supplier or an association, and its manager. */
export type RegistrationRequestCreate =
	| { supplier: SupplierCreate; account: AccountCreate }
	| { association: AssociationCreate; account: AccountCreate };

/** `RegistrationRequest` in the API contract. Either `supplier` or `association` is filled. */
export type RegistrationRequest = {
	id: number;
	status: "pending" | "approved" | "rejected";
	supplier: SupplierCreate | null;
	association: AssociationCreate | null;
	account: { firstname: string; lastname: string; email: string };
	// Supplier or association created once the request is approved, null until then.
	supplier_id: number | null;
	association_id: number | null;
	created_at: string;
	decided_at: string | null;
};

/** `LoginRequest` in the API contract. */
export type LoginRequest = {
	email: string;
	password: string;
};

/** `AuthTokens` in the API contract. */
export type AuthTokens = {
	access_token: string;
	refresh_token: string;
	token_type: "Bearer";
	// Lifetime of the access token, in seconds.
	expires_in: number;
};

/**
 * `POST /auth/login`: exchanges the credentials for a pair of tokens.
 * A 401 means wrong credentials, a 403 a registration request that is pending or rejected.
 */
export function login(credentials: LoginRequest): Promise<AuthTokens> {
	return apiRequest<AuthTokens>("/auth/login", {
		method: "POST",
		body: credentials,
	});
}

/**
 * `POST /registration-requests`: creates a `pending` request for a supplier or an association and
 * its manager.
 * A 409 means the e-mail, SIRET or RNA number is already used; a 422 a malformed field or an
 * address that cannot be found.
 */
export function createRegistrationRequest(
	request: RegistrationRequestCreate,
): Promise<RegistrationRequest> {
	return apiRequest<RegistrationRequest>("/registration-requests", {
		method: "POST",
		body: request,
	});
}

/**
 * `POST /auth/logout`: revokes the refresh token on the server. The route is authenticated, hence
 * the access token.
 */
export function logout(tokens: AuthTokens): Promise<void> {
	return apiRequest<void>("/auth/logout", {
		method: "POST",
		body: { refresh_token: tokens.refresh_token },
		accessToken: tokens.access_token,
	});
}
