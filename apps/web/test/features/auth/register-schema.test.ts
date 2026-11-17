import { describe, expect, it } from "vitest";

import {
	type RegisterFormValues,
	registerSchema,
} from "@/features/auth/register-schema";

const supplier: RegisterFormValues = {
	organization: {
		type: "supplier",
		name: "Cantine du lycée Ampère",
		legal_id: "19690103400017",
		supplier_type: "canteen",
		contact_phone: "04 78 00 00 00",
	},
	account: {
		firstname: "Marie",
		lastname: "Dupont",
		email: "marie.dupont@example.org",
		password: "motdepasse",
		password_confirmation: "motdepasse",
	},
};

function withOrganization(
	changes: Partial<RegisterFormValues["organization"]>,
) {
	return {
		...supplier,
		organization: { ...supplier.organization, ...changes },
	};
}

function withAccount(changes: Partial<RegisterFormValues["account"]>) {
	return { ...supplier, account: { ...supplier.account, ...changes } };
}

// Message of the issue reported on a field, e.g. "organization.legal_id".
function errorAt(values: RegisterFormValues, field: string) {
	const result = registerSchema.safeParse(values);
	return result.error?.issues.find((issue) => issue.path.join(".") === field)
		?.message;
}

describe("registerSchema", () => {
	it("turns supplier values into a supplier registration, without the password confirmation", () => {
		const result = registerSchema.safeParse(supplier);

		expect(result.data).toEqual({
			supplier: {
				name: "Cantine du lycée Ampère",
				legal_id: "19690103400017",
				supplier_type: "canteen",
				contact_phone: "04 78 00 00 00",
			},
			account: {
				firstname: "Marie",
				lastname: "Dupont",
				email: "marie.dupont@example.org",
				password: "motdepasse",
			},
		});
	});

	it("turns association values into an association registration, without establishment type", () => {
		const result = registerSchema.safeParse(
			withOrganization({
				type: "association",
				legal_id: "W691234567",
				supplier_type: "canteen",
			}),
		);

		expect(result.data).toEqual({
			association: {
				name: "Cantine du lycée Ampère",
				legal_id: "W691234567",
				contact_phone: "04 78 00 00 00",
			},
			account: {
				firstname: "Marie",
				lastname: "Dupont",
				email: "marie.dupont@example.org",
				password: "motdepasse",
			},
		});
	});

	it("requires the organization type", () => {
		expect(errorAt(withOrganization({ type: "" }), "organization.type")).toBe(
			"Choisissez le type de votre organisation.",
		);
	});

	it("requires a 14-digit SIRET for a supplier", () => {
		expect(
			errorAt(
				withOrganization({ legal_id: "W691234567" }),
				"organization.legal_id",
			),
		).toBe("Le SIRET doit contenir 14 chiffres.");
	});

	it("requires an RNA number for an association", () => {
		expect(
			errorAt(
				withOrganization({ type: "association", legal_id: "19690103400017" }),
				"organization.legal_id",
			),
		).toBe("Le n° RNA doit commencer par W, suivi de 9 chiffres.");
	});

	it("removes the spaces typed in the SIRET", () => {
		const result = registerSchema.safeParse(
			withOrganization({ legal_id: "196 901 034 00017" }),
		);

		expect(result.data).toMatchObject({
			supplier: { legal_id: "19690103400017" },
		});
	});

	it("requires the establishment type of a supplier", () => {
		expect(
			errorAt(
				withOrganization({ supplier_type: "" }),
				"organization.supplier_type",
			),
		).toBe("Choisissez le type d'établissement.");
	});

	it("requires a phone number of at least 10 characters", () => {
		expect(
			errorAt(
				withOrganization({ contact_phone: "0478" }),
				"organization.contact_phone",
			),
		).toBe("Le numéro de téléphone doit contenir au moins 10 caractères.");
	});

	it("requires the first name", () => {
		expect(errorAt(withAccount({ firstname: " " }), "account.firstname")).toBe(
			"Le prénom est obligatoire.",
		);
	});

	it("rejects a malformed e-mail", () => {
		expect(
			errorAt(withAccount({ email: "marie.dupont.org" }), "account.email"),
		).toBe("L'adresse e-mail est invalide.");
	});

	it("requires a password of at least 8 characters", () => {
		expect(
			errorAt(
				withAccount({ password: "abc", password_confirmation: "abc" }),
				"account.password",
			),
		).toBe("Le mot de passe doit contenir au moins 8 caractères.");
	});

	it("requires the confirmation to match the password", () => {
		expect(
			errorAt(
				withAccount({ password_confirmation: "autrechose" }),
				"account.password_confirmation",
			),
		).toBe("Les mots de passe ne correspondent pas.");
	});

	it("trims the text fields", () => {
		const result = registerSchema.safeParse(
			withAccount({
				firstname: " Marie ",
				email: " marie.dupont@example.org ",
			}),
		);

		expect(result.data?.account.firstname).toBe("Marie");
		expect(result.data?.account.email).toBe("marie.dupont@example.org");
	});
});
