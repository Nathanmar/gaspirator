import type { RegistrationRequest, RegistrationRequestCreate } from "@/features/auth/auth-api";

// Registrations as sent to and returned by `POST /registration-requests`.
// `satisfies` makes TypeScript check them against the contract types.

const account = {
  firstname: "Marie",
  lastname: "Dupont",
  email: "marie.dupont@example.org",
  password: "motdepasse",
} as const;

const address = { street: "12 rue de la République", postal_code: "69002", city: "Lyon" } as const;

export const supplierRegistration = {
  supplier: {
    name: "Cantine du lycée Ampère",
    legal_id: "19690103400017",
    supplier_type: "canteen",
    address,
    contact_phone: "04 78 00 00 00",
  },
  account,
} as const satisfies RegistrationRequestCreate;

export const associationRegistration = {
  association: {
    name: "Restos du Cœur Lyon 2",
    legal_id: "W691234567",
    address,
    contact_phone: "04 78 00 00 01",
  },
  account,
} as const satisfies RegistrationRequestCreate;

export const createdRegistration = {
  id: 18,
  status: "pending",
  supplier: supplierRegistration.supplier,
  association: null,
  account: { firstname: "Marie", lastname: "Dupont", email: "marie.dupont@example.org" },
  supplier_id: null,
  association_id: null,
  created_at: "2026-11-16T14:00:00Z",
  decided_at: null,
} as const satisfies RegistrationRequest;
