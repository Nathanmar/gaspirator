import { describe, expect, it } from "vitest";

import { loginSchema } from "@/features/auth/login-schema";

describe("loginSchema", () => {
	it("accepts a valid email and password", () => {
		const result = loginSchema.safeParse({
			email: "marie.dupont@example.org",
			password: "secret",
		});

		expect(result.success).toBe(true);
	});

	it("rejects an empty email", () => {
		const result = loginSchema.safeParse({ email: "", password: "secret" });

		expect(result.success).toBe(false);
		expect(result.error?.issues[0]?.path).toEqual(["email"]);
		expect(result.error?.issues[0]?.message).toBe(
			"L'adresse e-mail est obligatoire.",
		);
	});

	it("rejects a malformed email", () => {
		const result = loginSchema.safeParse({
			email: "marie.dupont.org",
			password: "secret",
		});

		expect(result.success).toBe(false);
		expect(result.error?.issues[0]?.path).toEqual(["email"]);
		expect(result.error?.issues[0]?.message).toBe(
			"L'adresse e-mail est invalide.",
		);
	});

	it("rejects an empty password", () => {
		const result = loginSchema.safeParse({
			email: "marie.dupont@example.org",
			password: "",
		});

		expect(result.success).toBe(false);
		expect(result.error?.issues[0]?.path).toEqual(["password"]);
		expect(result.error?.issues[0]?.message).toBe(
			"Le mot de passe est obligatoire.",
		);
	});

	it("trims the spaces around the email", () => {
		const result = loginSchema.safeParse({
			email: " marie.dupont@example.org ",
			password: "secret",
		});

		expect(result.success).toBe(true);
		expect(result.data?.email).toBe("marie.dupont@example.org");
	});

	it("accepts a short password", () => {
		const result = loginSchema.safeParse({
			email: "marie.dupont@example.org",
			password: "abc",
		});

		expect(result.success).toBe(true);
		expect(result.data?.password).toBe("abc");
	});
});
