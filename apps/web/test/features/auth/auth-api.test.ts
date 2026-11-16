import { describe, expect, it, vi } from "vitest";

import { login } from "@/features/auth/auth-api";
import { ApiError, NetworkError } from "@/lib/api-client";

import { jsonResponse, mockFetch } from "../../utils/fetch";

const credentials = { email: "marie.dupont@example.org", password: "secret" };

const tokens = {
  access_token: "access",
  refresh_token: "refresh",
  token_type: "Bearer",
  expires_in: 900,
};

const FALLBACK_MESSAGE = "Une erreur inattendue est survenue. Réessayez plus tard.";

describe("login", () => {
  it("posts the credentials as JSON to /auth/login", async () => {
    const fetchMock = mockFetch(jsonResponse(200, tokens));

    await login(credentials);

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/auth/login");
    expect(init?.method).toBe("POST");
    expect(new Headers(init?.headers).get("Content-Type")).toBe("application/json");
    expect(JSON.parse(String(init?.body))).toEqual(credentials);
  });

  it("returns the tokens sent by the API", async () => {
    mockFetch(jsonResponse(200, tokens));

    const result = await login(credentials);

    expect(result).toEqual(tokens);
  });

  it("throws an ApiError with the status and the contract error on 401", async () => {
    mockFetch(
      jsonResponse(401, { code: "unauthorized", message: "E-mail ou mot de passe incorrect." }),
    );

    const error = await login(credentials).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 401,
      code: "unauthorized",
      message: "E-mail ou mot de passe incorrect.",
    });
  });

  it("throws an ApiError on 403 when the registration is not approved", async () => {
    mockFetch(
      jsonResponse(403, {
        code: "forbidden",
        message: "Votre demande d'inscription est en attente de validation.",
      }),
    );

    const error = await login(credentials).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 403,
      code: "forbidden",
      message: "Votre demande d'inscription est en attente de validation.",
    });
  });

  it("keeps the field details of a validation error", async () => {
    const details = [{ field: "email", message: "adresse e-mail invalide" }];
    mockFetch(
      jsonResponse(422, {
        code: "validation_error",
        message: "Certains champs sont invalides.",
        details,
      }),
    );

    const error = await login(credentials).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 422, code: "validation_error", details });
  });

  it("throws an ApiError with a fallback message when the JSON error is not in the contract format", async () => {
    // FastAPI's default error format, still returned by the routes outside the contract.
    mockFetch(jsonResponse(404, { detail: "Not Found" }));

    const error = await login(credentials).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 404,
      code: null,
      message: FALLBACK_MESSAGE,
      details: [],
    });
  });

  it("throws an ApiError with a fallback message when the error body is not JSON", async () => {
    mockFetch(new Response("Bad Gateway", { status: 502 }));

    const error = await login(credentials).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 502, code: null, message: FALLBACK_MESSAGE });
  });

  it("throws a NetworkError when the server cannot be reached", async () => {
    const failure = new TypeError("Failed to fetch");
    globalThis.fetch = vi.fn<typeof fetch>().mockRejectedValue(failure);

    const error = await login(credentials).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(NetworkError);
    expect(error).toMatchObject({
      message: "Impossible de joindre le serveur. Vérifiez votre connexion.",
    });
    expect(error).toHaveProperty("cause", failure);
  });
});
