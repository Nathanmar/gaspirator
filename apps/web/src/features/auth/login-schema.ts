import { z } from "zod";

/**
 * Validation du formulaire de connexion, alignée sur `LoginRequest` du contrat (`openapi.yaml`).
 */
export const loginSchema = z.object({
  // Espaces retirés avant validation : les claviers mobiles en ajoutent souvent un en fin de saisie.
  // `z.email()` via `pipe` (et non `.email()`, déprécié dans zod 4) : il ne s'exécute que si
  // le champ est rempli, l'utilisateur ne voit donc qu'une seule erreur à la fois.
  email: z
    .string()
    .trim()
    .min(1, "L'adresse e-mail est obligatoire.")
    .pipe(z.email("L'adresse e-mail est invalide.")),
  // Ni trim (un espace peut faire partie du mot de passe), ni longueur minimale : le contrat
  // n'impose 8 caractères qu'à la création de compte (`AccountCreate`), pas à la connexion.
  password: z.string().min(1, "Le mot de passe est obligatoire."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
