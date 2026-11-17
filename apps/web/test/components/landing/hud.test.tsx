import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Hud } from "@/components/landing/hud";
import { useAuthStore } from "@/features/auth/auth-store";

import { tokens } from "../../fixtures/auth";
import { jsonResponse, mockFetch } from "../../utils/fetch";
import { renderWithRouter } from "../../utils/render-with-router";

beforeEach(() => {
  useAuthStore.setState({ tokens: null });
});

describe("Hud", () => {
  it("sends the join button to the registration page", async () => {
    renderWithRouter(<Hud />);

    expect(await screen.findByRole("link", { name: "Rejoindre" })).toHaveAttribute(
      "href",
      "/register",
    );
  });

  it("shows a logout button instead of the join button once logged in", async () => {
    useAuthStore.setState({ tokens });
    renderWithRouter(<Hud />);

    expect(await screen.findByRole("button", { name: "Se déconnecter" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Rejoindre" })).not.toBeInTheDocument();
  });

  it("logs out on the API, forgets the tokens and shows the join button again", async () => {
    useAuthStore.setState({ tokens });
    const fetchMock = mockFetch(new Response(null, { status: 204 }));
    renderWithRouter(<Hud />);

    await userEvent.click(await screen.findByRole("button", { name: "Se déconnecter" }));

    expect(await screen.findByRole("link", { name: "Rejoindre" })).toBeInTheDocument();
    expect(useAuthStore.getState().tokens).toBeNull();
    expect(fetchMock.mock.calls[0][0]).toBe("http://api.test/auth/logout");
  });

  it("ends the session anyway when the API refuses the logout (expired token)", async () => {
    useAuthStore.setState({ tokens });
    mockFetch(
      jsonResponse(401, { code: "unauthorized", message: "Token d'accès invalide ou expiré." }),
    );
    renderWithRouter(<Hud />);

    await userEvent.click(await screen.findByRole("button", { name: "Se déconnecter" }));

    expect(await screen.findByRole("link", { name: "Rejoindre" })).toBeInTheDocument();
    expect(useAuthStore.getState().tokens).toBeNull();
  });

  it("sends a single logout request on a double tap", async () => {
    useAuthStore.setState({ tokens });
    // A logout that never answers, so the second tap happens while the first one is running.
    const fetchMock = vi.fn<typeof fetch>().mockReturnValue(new Promise(() => {}));
    globalThis.fetch = fetchMock;
    renderWithRouter(<Hud />);

    await userEvent.dblClick(await screen.findByRole("button", { name: "Se déconnecter" }));

    expect(fetchMock).toHaveBeenCalledOnce();
  });
});
