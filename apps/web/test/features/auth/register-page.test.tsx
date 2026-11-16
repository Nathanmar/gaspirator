import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RegisterPage } from "@/features/auth/register-page";

import { createdRegistration, registrationPayload } from "../../fixtures/registration";
import { jsonResponse, mockFetch, sentBody } from "../../utils/fetch";
import { renderWithRouter } from "../../utils/render-with-router";

// Fills the form of a supplier with the values of `registrationPayload`.
async function fillSupplierForm() {
  await userEvent.type(await screen.findByLabelText("Nom de l'organisation"), "Cantine du lycée Ampère");
  await userEvent.type(screen.getByLabelText("SIRET"), "19690103400017");
  await userEvent.selectOptions(screen.getByLabelText("Type d'établissement"), "Cantine");
  await userEvent.type(screen.getByLabelText("Adresse"), "12 rue de la République");
  await userEvent.type(screen.getByLabelText("Code postal"), "69002");
  await userEvent.type(screen.getByLabelText("Ville"), "Lyon");
  await userEvent.type(screen.getByLabelText("Téléphone"), "04 78 00 00 00");
  await userEvent.type(screen.getByLabelText("Prénom"), "Marie");
  await userEvent.type(screen.getByLabelText("Nom"), "Dupont");
  await userEvent.type(screen.getByLabelText("E-mail"), "marie.dupont@example.org");
  await userEvent.type(screen.getByLabelText("Mot de passe"), "motdepasse");
  await userEvent.type(screen.getByLabelText("Confirmation du mot de passe"), "motdepasse");
}

function submit() {
  return userEvent.click(screen.getByRole("button", { name: "Envoyer ma demande" }));
}

describe("RegisterPage", () => {
  it("preselects the organization type chosen on the landing page", async () => {
    renderWithRouter(<RegisterPage role="association" />, { path: "/register" });

    expect(await screen.findByRole("radio", { name: "Association" })).toBeChecked();
    expect(screen.getByLabelText("N° RNA")).toBeInTheDocument();
    expect(screen.queryByLabelText("Type d'établissement")).not.toBeInTheDocument();
  });

  it("asks a supplier for a SIRET and an establishment type", async () => {
    renderWithRouter(<RegisterPage role="supplier" />, { path: "/register" });

    expect(await screen.findByLabelText("SIRET")).toBeInTheDocument();
    expect(screen.getByLabelText("Type d'établissement")).toBeInTheDocument();
  });

  it("links to the login page with the same role", async () => {
    renderWithRouter(<RegisterPage role="supplier" />, { path: "/register" });

    expect(await screen.findByRole("link", { name: "Se connecter" })).toHaveAttribute(
      "href",
      "/login?role=supplier",
    );
  });

  it("shows the errors and sends nothing when the form is empty", async () => {
    const fetchMock = mockFetch(jsonResponse(201, createdRegistration));
    renderWithRouter(<RegisterPage />, { path: "/register" });

    await screen.findByRole("button", { name: "Envoyer ma demande" });
    await submit();

    expect(await screen.findByText("Choisissez le type de votre organisation.")).toBeInTheDocument();
    expect(screen.getByText("Le prénom est obligatoire.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("sends the request in the contract format and confirms it", async () => {
    const fetchMock = mockFetch(jsonResponse(201, createdRegistration));
    renderWithRouter(<RegisterPage role="supplier" />, { path: "/register" });

    await fillSupplierForm();
    await submit();

    expect(await screen.findByRole("heading", { name: "Demande envoyée" })).toBeInTheDocument();
    expect(sentBody(fetchMock)).toEqual(registrationPayload);
  });

  it("explains that the e-mail, SIRET or RNA number is already used (409)", async () => {
    mockFetch(jsonResponse(409, { code: "conflict", message: "Conflit." }));
    renderWithRouter(<RegisterPage role="supplier" />, { path: "/register" });

    await fillSupplierForm();
    await submit();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Un compte existe déjà avec cette adresse e-mail, ce SIRET ou ce n° RNA.",
    );
  });

  it("tells the user when the server cannot be reached", async () => {
    globalThis.fetch = vi.fn<typeof fetch>().mockRejectedValue(new TypeError("Failed to fetch"));
    renderWithRouter(<RegisterPage role="supplier" />, { path: "/register" });

    await fillSupplierForm();
    await submit();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Impossible de joindre le serveur. Vérifiez votre connexion.",
    );
  });
});
