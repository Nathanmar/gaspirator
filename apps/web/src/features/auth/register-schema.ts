import { z } from "zod";

import type { OrganizationType, RegistrationRequestCreate, SupplierType } from "./auth-api";

/**
 * Values of the registration form, before validation. Choices start empty ("") so the user has to
 * pick them; the password confirmation only exists in the form.
 */
export type RegisterFormValues = {
  organization: {
    type: OrganizationType | "";
    name: string;
    legal_id: string;
    supplier_type: SupplierType | "";
    address: { street: string; postal_code: string; city: string };
    contact_phone: string;
  };
  account: {
    firstname: string;
    lastname: string;
    email: string;
    password: string;
    password_confirmation: string;
  };
};

export const SUPPLIER_TYPES = ["canteen", "hospital", "supermarket", "other"] as const;

// Bounds and patterns below come from `RegistrationRequestCreate` in the API contract.

const addressSchema = z.object({
  street: z
    .string()
    .trim()
    .min(3, "L'adresse doit contenir au moins 3 caractères.")
    .max(255, "L'adresse doit contenir au plus 255 caractères."),
  postal_code: z
    .string()
    .trim()
    .regex(/^\d{5}$/, "Le code postal doit contenir 5 chiffres."),
  city: z
    .string()
    .trim()
    .min(1, "La ville est obligatoire.")
    .max(120, "La ville doit contenir au plus 120 caractères."),
});

const commonOrganizationFields = {
  name: z
    .string()
    .trim()
    .min(2, "Le nom de l'organisation doit contenir au moins 2 caractères.")
    .max(255, "Le nom de l'organisation doit contenir au plus 255 caractères."),
  address: addressSchema,
  contact_phone: z
    .string()
    .trim()
    .min(10, "Le numéro de téléphone doit contenir au moins 10 caractères.")
    .max(20, "Le numéro de téléphone doit contenir au plus 20 caractères."),
};

// Spaces are allowed while typing ("196 901 034 00017") and removed before checking the format.
const legalId = z.string().transform((value) => value.replace(/\s/g, "").toUpperCase());

// Step 2 of the form. One branch per organization type: the legal ID format and the establishment
// type depend on it.
export const organizationSchema = z.discriminatedUnion(
  "type",
  [
    z.object({
      type: z.literal("supplier"),
      ...commonOrganizationFields,
      legal_id: legalId.pipe(z.string().regex(/^\d{14}$/, "Le SIRET doit contenir 14 chiffres.")),
      supplier_type: z.enum(SUPPLIER_TYPES, "Choisissez le type d'établissement."),
    }),
    z.object({
      type: z.literal("association"),
      ...commonOrganizationFields,
      legal_id: legalId.pipe(
        z.string().regex(/^W\d{9}$/, "Le n° RNA doit commencer par W, suivi de 9 chiffres."),
      ),
      // An association has no establishment type: whatever was picked before switching to
      // "association" is accepted here and left out of the request.
      supplier_type: z.union([z.enum(SUPPLIER_TYPES), z.literal("")]),
    }),
  ],
  { error: "Choisissez le type de votre organisation." },
);

// Step 1 of the form: the manager's account.
export const accountSchema = z
  .object({
    firstname: z
      .string()
      .trim()
      .min(1, "Le prénom est obligatoire.")
      .max(255, "Le prénom doit contenir au plus 255 caractères."),
    lastname: z
      .string()
      .trim()
      .min(1, "Le nom est obligatoire.")
      .max(255, "Le nom doit contenir au plus 255 caractères."),
    email: z
      .string()
      .trim()
      .min(1, "L'adresse e-mail est obligatoire.")
      .max(255, "L'adresse e-mail doit contenir au plus 255 caractères.")
      .pipe(z.email("L'adresse e-mail est invalide.")),
    password: z
      .string()
      .min(8, "Le mot de passe doit contenir au moins 8 caractères.")
      .max(128, "Le mot de passe doit contenir au plus 128 caractères."),
    password_confirmation: z.string(),
  })
  .refine((account) => account.password === account.password_confirmation, {
    path: ["password_confirmation"],
    message: "Les mots de passe ne correspondent pas.",
  });

/**
 * Registration form validation. Its output is the `RegistrationRequestCreate` body of the API:
 * `{ supplier, account }` or `{ association, account }`, without the password confirmation.
 */
export const registerSchema = z
  .object({ organization: organizationSchema, account: accountSchema })
  .transform(({ organization, account }): RegistrationRequestCreate => {
    const manager = {
      firstname: account.firstname,
      lastname: account.lastname,
      email: account.email,
      password: account.password,
    };
    const fields = {
      name: organization.name,
      legal_id: organization.legal_id,
      address: organization.address,
      contact_phone: organization.contact_phone,
    };

    return organization.type === "supplier"
      ? { supplier: { ...fields, supplier_type: organization.supplier_type }, account: manager }
      : { association: fields, account: manager };
  });
