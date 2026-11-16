// A supplier's registration, as sent to and returned by `POST /registration-requests`.

export const registrationPayload = {
  organization: {
    type: "supplier",
    name: "Cantine du lycée Ampère",
    legal_id: "19690103400017",
    supplier_type: "canteen",
    address: { street: "12 rue de la République", postal_code: "69002", city: "Lyon" },
    contact_phone: "04 78 00 00 00",
  },
  account: {
    firstname: "Marie",
    lastname: "Dupont",
    email: "marie.dupont@example.org",
    password: "motdepasse",
  },
} as const;

export const createdRegistration = {
  id: 18,
  status: "pending",
  organization: registrationPayload.organization,
  account: { firstname: "Marie", lastname: "Dupont", email: "marie.dupont@example.org" },
  organization_id: null,
  created_at: "2026-11-16T14:00:00Z",
  decided_at: null,
} as const;
