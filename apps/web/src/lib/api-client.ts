import { env } from "@gaspirator/env/web";
import { z } from "zod";

/**
 * `Error` schema of the API contract (`openapi.yaml`), returned by every failed request.
 */
const apiErrorBodySchema = z.object({
  code: z.enum([
    "bad_request",
    "unauthorized",
    "forbidden",
    "not_found",
    "validation_error",
    "conflict",
    "too_many_requests",
  ]),
  message: z.string(),
  details: z.array(z.object({ field: z.string(), message: z.string() })).optional(),
});

type ApiErrorBody = z.infer<typeof apiErrorBodySchema>;

export type ApiErrorCode = ApiErrorBody["code"];
export type ApiErrorDetail = NonNullable<ApiErrorBody["details"]>[number];

const FALLBACK_MESSAGE = "Une erreur inattendue est survenue. Réessayez plus tard.";
const NETWORK_MESSAGE = "Impossible de joindre le serveur. Vérifiez votre connexion.";

/**
 * The API answered with an error status. `code` is null when the body does not follow the
 * contract format; `message` then falls back to a generic text that can be shown to the user.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: ApiErrorCode | null;
  readonly details: ApiErrorDetail[];

  constructor(status: number, body: ApiErrorBody | null) {
    super(body?.message ?? FALLBACK_MESSAGE);
    this.name = "ApiError";
    this.status = status;
    this.code = body?.code ?? null;
    this.details = body?.details ?? [];
  }
}

/**
 * The request got no answer at all (offline, server down, CORS refusal…).
 * The original error is kept in `cause` for debugging.
 */
export class NetworkError extends Error {
  constructor(options?: ErrorOptions) {
    super(NETWORK_MESSAGE, options);
    this.name = "NetworkError";
  }
}

type ApiRequestOptions = {
  // The contract only uses these two methods.
  method: "GET" | "POST";
  // Serialized as JSON.
  body?: unknown;
};

/**
 * Calls an endpoint of the API contract and returns its JSON response.
 *
 * @throws {ApiError} when the API answers with an error status.
 * @throws {NetworkError} when the API cannot be reached.
 */
export async function apiRequest<T>(path: string, { method, body }: ApiRequestOptions): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${env.VITE_API_URL}${path}`, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (error) {
    throw new NetworkError({ cause: error });
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readErrorBody(response));
  }

  return (await response.json()) as T;
}

async function readErrorBody(response: Response): Promise<ApiErrorBody | null> {
  // The body may not be JSON at all (HTML page from a proxy, empty body…).
  const json: unknown = await response.json().catch(() => null);
  const result = apiErrorBodySchema.safeParse(json);
  return result.success ? result.data : null;
}
