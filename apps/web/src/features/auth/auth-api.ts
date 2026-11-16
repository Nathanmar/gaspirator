import { apiRequest } from "@/lib/api-client";

/** `OrganizationType` in the API contract. */
export type OrganizationType = "supplier" | "association";

/** `SupplierType` in the API contract: kind of establishment of a supplier. */
export type SupplierType = "canteen" | "hospital" | "supermarket" | "other";

/** `RegistrationRequestCreate` in the API contract. */
export type RegistrationRequestCreate = {
  organization: {
    type: OrganizationType;
    name: string;
    // SIRET (14 digits) for a supplier, RNA number (W + 9 digits) for an association.
    legal_id: string;
    // Required for a supplier, null for an association.
    supplier_type: SupplierType | null;
    address: { street: string; postal_code: string; city: string };
    contact_phone: string;
  };
  account: { firstname: string; lastname: string; email: string; password: string };
};

/** `RegistrationRequest` in the API contract. */
export type RegistrationRequest = {
  id: number;
  status: "pending" | "approved" | "rejected";
  organization: RegistrationRequestCreate["organization"];
  account: { firstname: string; lastname: string; email: string };
  // Organization created once the request is approved, null until then.
  organization_id: number | null;
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
  return apiRequest<AuthTokens>("/auth/login", { method: "POST", body: credentials });
}

/**
 * `POST /registration-requests`: creates a `pending` request for an organization and its manager.
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
