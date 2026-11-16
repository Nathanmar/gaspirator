import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/features/auth/login-form";

describe("LoginForm", () => {
  it("shows the email and password fields and a submit button", () => {
    render(<LoginForm onSubmit={vi.fn()} />);

    expect(screen.getByLabelText("E-mail")).toHaveAttribute("type", "email");
    expect(screen.getByLabelText("Mot de passe")).toHaveAttribute("type", "password");
    expect(screen.getByRole("button", { name: "Se connecter" })).toBeInTheDocument();
  });

  it("shows the validation errors and does not submit an empty form", async () => {
    const onSubmit = vi.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    await userEvent.click(screen.getByRole("button", { name: "Se connecter" }));

    expect(await screen.findByText("L'adresse e-mail est obligatoire.")).toBeInTheDocument();
    expect(screen.getByText("Le mot de passe est obligatoire.")).toBeInTheDocument();
    expect(screen.getByLabelText("E-mail")).toHaveAttribute("aria-invalid", "true");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows an error for a malformed email", async () => {
    render(<LoginForm onSubmit={vi.fn()} />);

    await userEvent.type(screen.getByLabelText("E-mail"), "marie.dupont.org");
    await userEvent.type(screen.getByLabelText("Mot de passe"), "secret");
    await userEvent.click(screen.getByRole("button", { name: "Se connecter" }));

    expect(await screen.findByText("L'adresse e-mail est invalide.")).toBeInTheDocument();
  });

  it("submits the trimmed email and the password", async () => {
    const onSubmit = vi.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText("E-mail"), " marie.dupont@example.org ");
    await userEvent.type(screen.getByLabelText("Mot de passe"), "secret");
    await userEvent.click(screen.getByRole("button", { name: "Se connecter" }));

    await vi.waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        email: "marie.dupont@example.org",
        password: "secret",
      }),
    );
  });
});
