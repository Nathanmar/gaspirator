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
