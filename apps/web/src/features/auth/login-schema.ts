import { z } from "zod";

/**
 * Login form validation, aligned with `LoginRequest` in the API contract (`openapi.yaml`).
 */
export const loginSchema = z.object({
	// Trimmed before validation: mobile keyboards often append a trailing space.
	// `z.email()` through `pipe` (not `.email()`, deprecated in zod 4) only runs once the field
	// is filled in, so the user sees a single error at a time.
	email: z
		.string()
		.trim()
		.min(1, "L'adresse e-mail est obligatoire.")
		.pipe(z.email("L'adresse e-mail est invalide.")),
	// No trim (a space can be part of a password) and no minimum length: the contract only
	// requires 8 characters when creating an account (`AccountCreate`), not when logging in.
	password: z.string().min(1, "Le mot de passe est obligatoire."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
