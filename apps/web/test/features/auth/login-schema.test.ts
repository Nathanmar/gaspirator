import { describe, expect, it } from "vitest";

import { loginSchema } from "@/features/auth/login-schema";

describe("loginSchema", async () => {
  it("accepte un e-mail et un mot de passe valides", () => {
    const result = loginSchema.safeParse({
      email: "marie.dupont@example.org",
      password: "secret",
    });

    expect(result.success).toBe(true);
  });

  it("refuse un e-mail vide", async () => {
    const result = loginSchema.safeParse({ email: "", password: "secret" });

    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.path).toEqual(["email"]);
    expect(result.error?.issues[0]?.message).toBe("L'adresse e-mail est obligatoire.");
  });

  it("refuse un e-mail mal formé", async () => {
    const result = loginSchema.safeParse({
      email: "marie.dupont.org",
      password: "secret",
    });

    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.path).toEqual(["email"]);
    expect(result.error?.issues[0]?.message).toBe("L'adresse e-mail est invalide.");
  });

  it("refuse un mot de passe vide", async () => {
    const result = loginSchema.safeParse({ email: "marie.dupont@example.org", password: "" });

    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.path).toEqual(["password"]);
    expect(result.error?.issues[0]?.message).toBe("Le mot de passe est obligatoire.");
  });

  it("retire les espaces autour de l'e-mail", async () => {
    const result = loginSchema.safeParse({
      email: " marie.dupont@example.org ",
      password: "secret",
    });

    expect(result.success).toBe(true);
    expect(result.data?.email).toBe("marie.dupont@example.org");
  });

  it("accepte un mot de passe court", async () => {
    const result = loginSchema.safeParse({
      email: "marie.dupont@example.org",
      password: "abc",
    });

    expect(result.success).toBe(true);
    expect(result.data?.password).toBe("abc");
  });
});
