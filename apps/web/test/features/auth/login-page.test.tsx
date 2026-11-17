import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginPage } from "@/features/auth/login-page";
import { useAuthStore } from "@/features/auth/auth-store";

import { tokens } from "../../fixtures/auth";
import { jsonResponse, mockFetch, sentBody } from "../../utils/fetch";
import { renderWithRouter } from "../../utils/render-with-router";

beforeEach(() => {
  useAuthStore.setState({ tokens: null });
});

async function logIn() {
  await userEvent.type(await screen.findByLabelText("E-mail"), "marie.dupont@example.org");
  await userEvent.type(screen.getByLabelText("Mot de passe"), "secret");
  await userEvent.click(screen.getByRole("button", { name: "Se connecter" }));
}

describe("LoginPage", () => {
  it("shows the space of the role chosen on the landing page", async () => {
    renderWithRouter(<LoginPage role="supplier" />, { path: "/login" });

    expect(await screen.findByText("Espace fournisseur")).toBeInTheDocument();
  });

  it("links to the registration page with the same role", async () => {
    renderWithRouter(<LoginPage role="association" />, { path: "/login" });

    expect(await screen.findByRole("link", { name: "Créer un compte" })).toHaveAttribute(
      "href",
      "/register?role=association",
    );
  });

  it("stores the tokens and goes to the home page once logged in", async () => {
    const fetchMock = mockFetch(jsonResponse(200, tokens));
    const router = renderWithRouter(<LoginPage />, { path: "/login" });

    await logIn();

    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
    expect(sentBody(fetchMock)).toEqual({ email: "marie.dupont@example.org", password: "secret" });
    expect(useAuthStore.getState().tokens).toEqual(tokens);
  });

  it("shows its own generic message on wrong credentials (401)", async () => {
    mockFetch(jsonResponse(401, { code: "unauthorized", message: "Identifiants invalides." }));
    renderWithRouter(<LoginPage />, { path: "/login" });

    await logIn();

    expect(await screen.findByRole("alert")).toHaveTextContent("E-mail ou mot de passe incorrect.");
    expect(useAuthStore.getState().tokens).toBeNull();
  });

  it("shows the server's explanation when the account is not active yet (403)", async () => {
    mockFetch(
      jsonResponse(403, {
        code: "forbidden",
        message: "Votre demande d'inscription est en attente de validation.",
      }),
    );
    renderWithRouter(<LoginPage />, { path: "/login" });

    await logIn();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Votre demande d'inscription est en attente de validation.",
    );
  });

  it("tells the user when the server cannot be reached", async () => {
    globalThis.fetch = vi.fn<typeof fetch>().mockRejectedValue(new TypeError("Failed to fetch"));
    renderWithRouter(<LoginPage />, { path: "/login" });

    await logIn();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Impossible de joindre le serveur. Vérifiez votre connexion.",
    );
  });
});
