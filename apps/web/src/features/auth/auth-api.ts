import { apiRequest } from "@/lib/api-client";

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
