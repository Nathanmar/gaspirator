import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RegisterPage } from "@/features/auth/register-page";

import {
  associationRegistration,
  createdRegistration,
  supplierRegistration,
} from "../../fixtures/registration";
import { jsonResponse, mockFetch, sentBody } from "../../utils/fetch";
import { renderWithRouter } from "../../utils/render-with-router";

// Step 1: the manager's account, with the values of the fixtures.
async function fillAccountStep() {
  await userEvent.type(await screen.findByLabelText("Prénom"), "Marie");
  await userEvent.type(screen.getByLabelText("Nom"), "Dupont");
  await userEvent.type(screen.getByLabelText("E-mail"), "marie.dupont@example.org");
  await userEvent.type(screen.getByLabelText("Mot de passe"), "motdepasse");
  await userEvent.type(screen.getByLabelText("Confirmation du mot de passe"), "motdepasse");
  await userEvent.click(screen.getByRole("button", { name: "Continuer" }));
}

// Step 2: a supplier, with the values of `supplierRegistration`.
async function fillSupplierStep() {
  await userEvent.type(
    await screen.findByLabelText("Nom de l'organisation"),
    "Cantine du lycée Ampère",
  );
  await userEvent.type(screen.getByLabelText("SIRET"), "19690103400017");
  await userEvent.click(screen.getByLabelText("Type d'établissement"));
  await userEvent.click(await screen.findByRole("option", { name: "Cantine" }));
  await userEvent.type(screen.getByLabelText("Adresse"), "12 rue de la République");
  await userEvent.type(screen.getByLabelText("Code postal"), "69002");
  await userEvent.type(screen.getByLabelText("Ville"), "Lyon");
  await userEvent.type(screen.getByLabelText("Téléphone"), "04 78 00 00 00");
}

// Step 2: an association, with the values of `associationRegistration`.
async function fillAssociationStep() {
  await userEvent.type(
    await screen.findByLabelText("Nom de l'organisation"),
    "Restos du Cœur Lyon 2",
  );
  await userEvent.type(screen.getByLabelText("N° RNA"), "W691234567");
  await userEvent.type(screen.getByLabelText("Adresse"), "12 rue de la République");
  await userEvent.type(screen.getByLabelText("Code postal"), "69002");
  await userEvent.type(screen.getByLabelText("Ville"), "Lyon");
  await userEvent.type(screen.getByLabelText("Téléphone"), "04 78 00 00 01");
}

function submit() {
  return userEvent.click(screen.getByRole("button", { name: "Envoyer ma demande" }));
}

describe("RegisterPage", () => {
  it("starts with the account step", async () => {
    renderWithRouter(<RegisterPage />, { path: "/register" });

    expect(await screen.findByRole("heading", { name: "Votre compte" })).toBeInTheDocument();
    expect(screen.getByText("Étape 1 sur 2")).toBeInTheDocument();
    expect(screen.queryByLabelText("Nom de l'organisation")).not.toBeInTheDocument();
  });

  it("stays on the account step while it is invalid", async () => {
    renderWithRouter(<RegisterPage />, { path: "/register" });

    await userEvent.click(await screen.findByRole("button", { name: "Continuer" }));

    expect(await screen.findByText("Le prénom est obligatoire.")).toBeInTheDocument();
    expect(screen.queryByLabelText("Nom de l'organisation")).not.toBeInTheDocument();
  });

  it("goes on to the organization step once the account is valid", async () => {
    renderWithRouter(<RegisterPage />, { path: "/register" });

    await fillAccountStep();

    expect(await screen.findByRole("heading", { name: "Votre organisation" })).toBeInTheDocument();
    expect(screen.getByText("Étape 2 sur 2")).toBeInTheDocument();
  });

  it("keeps the account values when going back", async () => {
    renderWithRouter(<RegisterPage />, { path: "/register" });

    await fillAccountStep();
    await userEvent.click(await screen.findByRole("button", { name: "Retour" }));

    expect(await screen.findByLabelText("E-mail")).toHaveValue("marie.dupont@example.org");
  });

  it("preselects the organization type chosen on the landing page", async () => {
    renderWithRouter(<RegisterPage role="association" />, { path: "/register" });

    await fillAccountStep();

    expect(await screen.findByRole("radio", { name: "Association" })).toBeChecked();
    expect(screen.getByLabelText("N° RNA")).toBeInTheDocument();
    expect(screen.queryByLabelText("Type d'établissement")).not.toBeInTheDocument();
  });

  it("asks a supplier for a SIRET and an establishment type", async () => {
    renderWithRouter(<RegisterPage role="supplier" />, { path: "/register" });

    await fillAccountStep();

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

  it("shows the errors and sends nothing when the organization step is empty", async () => {
    const fetchMock = mockFetch(jsonResponse(201, createdRegistration));
    renderWithRouter(<RegisterPage />, { path: "/register" });

    await fillAccountStep();
    await screen.findByRole("heading", { name: "Votre organisation" });
    await submit();

    expect(await screen.findByText("Choisissez le type de votre organisation.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("sends a supplier registration in the contract format and confirms it", async () => {
    const fetchMock = mockFetch(jsonResponse(201, createdRegistration));
    renderWithRouter(<RegisterPage role="supplier" />, { path: "/register" });

    await fillAccountStep();
    await fillSupplierStep();
    await submit();

    expect(await screen.findByRole("heading", { name: "Demande envoyée" })).toBeInTheDocument();
    expect(screen.getByText("Cantine du lycée Ampère")).toBeInTheDocument();
    expect(sentBody(fetchMock)).toEqual(supplierRegistration);
  });

  it("sends an association registration in the contract format and confirms it", async () => {
    // The mock server answers with a fixed example (here, a supplier's): the confirmation must
    // repeat what was sent, not read the response.
    const fetchMock = mockFetch(jsonResponse(201, createdRegistration));
    renderWithRouter(<RegisterPage role="association" />, { path: "/register" });

    await fillAccountStep();
    await fillAssociationStep();
    await submit();

    expect(await screen.findByRole("heading", { name: "Demande envoyée" })).toBeInTheDocument();
    expect(screen.getByText("Restos du Cœur Lyon 2")).toBeInTheDocument();
    expect(sentBody(fetchMock)).toEqual(associationRegistration);
  });

  it("shows the server's explanation of what is already used (409)", async () => {
    mockFetch(
      jsonResponse(409, { code: "conflict", message: "Ce SIRET ou ce n° RNA est déjà utilisé." }),
    );
    renderWithRouter(<RegisterPage role="supplier" />, { path: "/register" });

    await fillAccountStep();
    await fillSupplierStep();
    await submit();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Ce SIRET ou ce n° RNA est déjà utilisé.",
    );
  });

  it("lists the fields refused by the server (422)", async () => {
    mockFetch(
      jsonResponse(422, {
        code: "validation_error",
        message: "Certains champs sont invalides.",
        details: [
          { field: "account.email", message: "adresse e-mail invalide" },
          { field: "supplier.address", message: "adresse introuvable" },
        ],
      }),
    );
    renderWithRouter(<RegisterPage role="supplier" />, { path: "/register" });

    await fillAccountStep();
    await fillSupplierStep();
    await submit();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Certaines informations ont été refusées");
    expect(alert).toHaveTextContent("E-mail : adresse e-mail invalide");
    expect(alert).toHaveTextContent("Adresse : adresse introuvable");
  });

  it("tells the user when the server cannot be reached", async () => {
    globalThis.fetch = vi.fn<typeof fetch>().mockRejectedValue(new TypeError("Failed to fetch"));
    renderWithRouter(<RegisterPage role="supplier" />, { path: "/register" });

    await fillAccountStep();
    await fillSupplierStep();
    await submit();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Impossible de joindre le serveur. Vérifiez votre connexion.",
    );
  });
});
