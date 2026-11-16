import type { ComponentProps, ReactNode } from "react";

import { type AnyFieldApi, revalidateLogic, useForm, useStore } from "@tanstack/react-form";

import {
  ChoiceField,
  FormAlert,
  SelectField,
  SubmitButton,
  TextField,
} from "@/components/form-controls";

import type { OrganizationType, RegistrationRequestCreate, SupplierType } from "./auth-api";
import { type RegisterFormValues, SUPPLIER_TYPES, registerSchema } from "./register-schema";

const ORGANIZATION_TYPES = [
  { value: "supplier", label: "Fournisseur", tone: "lime" },
  { value: "association", label: "Association", tone: "tomato" },
] as const;

const SUPPLIER_TYPE_LABELS: Record<SupplierType, string> = {
  canteen: "Cantine",
  hospital: "Hôpital",
  supermarket: "Supermarché",
  other: "Autre",
};

const LEGAL_ID_LABELS: Record<OrganizationType | "", string> = {
  supplier: "SIRET",
  association: "N° RNA",
  "": "SIRET ou n° RNA",
};

function emptyValues(type: OrganizationType | ""): RegisterFormValues {
  return {
    organization: {
      type,
      name: "",
      legal_id: "",
      supplier_type: "",
      address: { street: "", postal_code: "", city: "" },
      contact_phone: "",
    },
    account: { firstname: "", lastname: "", email: "", password: "", password_confirmation: "" },
  };
}

// "organization.address.city" -> "organization-address-city", a tidier HTML id.
function fieldId(name: string) {
  return name.replaceAll(".", "-");
}

function firstError(field: AnyFieldApi): string | undefined {
  return field.state.meta.errors[0]?.message;
}

/** Text input wired to a TanStack Form field. */
function BoundTextField({
  field,
  ...props
}: { field: AnyFieldApi; label: string } & Omit<
  ComponentProps<typeof TextField>,
  "id" | "name" | "value" | "onChange" | "onBlur" | "error"
>) {
  return (
    <TextField
      id={fieldId(field.name)}
      name={field.name}
      value={field.state.value}
      onBlur={field.handleBlur}
      onChange={(e) => field.handleChange(e.target.value)}
      error={firstError(field)}
      {...props}
    />
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-5">
      <h2 className="text-2xl font-extrabold tracking-[-0.03em]">{title}</h2>
      {children}
    </section>
  );
}

type RegisterFormProps = {
  // Organization type chosen on the landing page, preselected.
  defaultType?: OrganizationType;
  // Error of the whole form, shown next to the submit button where the user is looking.
  error?: string | null;
  // While the returned promise is pending, the submit button is disabled.
  onSubmit: (request: RegistrationRequestCreate) => void | Promise<void>;
};

export function RegisterForm({ defaultType, error, onSubmit }: RegisterFormProps) {
  const form = useForm({
    defaultValues: emptyValues(defaultType ?? ""),
    // Validate on submit first, then on every change so an error goes away as soon as it is fixed.
    validationLogic: revalidateLogic(),
    validators: { onDynamic: registerSchema },
    // The schema output is the request body of the contract (trimmed, without the confirmation).
    onSubmit: ({ value }) => onSubmit(registerSchema.parse(value)),
  });
  // The legal ID label and the establishment type depend on the organization type.
  const type = useStore(form.store, (state) => state.values.organization.type);

  return (
    <form
      noValidate
      className="flex flex-col gap-10"
      onSubmit={(e) => {
        e.preventDefault();
        void form.handleSubmit();
      }}
    >
      <Section title="Votre organisation">
        <form.Field name="organization.type">
          {(field) => (
            <ChoiceField
              name={field.name}
              legend="Type d'organisation"
              options={ORGANIZATION_TYPES}
              value={field.state.value}
              onChange={(value) => field.handleChange(value)}
              onBlur={field.handleBlur}
              error={firstError(field)}
            />
          )}
        </form.Field>

        <form.Field name="organization.name">
          {(field) => (
            <BoundTextField field={field} label="Nom de l'organisation" autoComplete="organization" />
          )}
        </form.Field>

        <form.Field name="organization.legal_id">
          {(field) => (
            <BoundTextField
              field={field}
              label={LEGAL_ID_LABELS[type]}
              autoComplete="off"
              // A SIRET is only digits: show the numeric keypad on mobile.
              inputMode={type === "supplier" ? "numeric" : "text"}
              placeholder={type === "association" ? "W123456789" : undefined}
            />
          )}
        </form.Field>

        {type === "supplier" && (
          <form.Field name="organization.supplier_type">
            {(field) => (
              <SelectField
                id={fieldId(field.name)}
                name={field.name}
                label="Type d'établissement"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={(e) => field.handleChange(e.target.value as SupplierType | "")}
                error={firstError(field)}
              >
                <option value="">Choisir…</option>
                {SUPPLIER_TYPES.map((supplierType) => (
                  <option key={supplierType} value={supplierType}>
                    {SUPPLIER_TYPE_LABELS[supplierType]}
                  </option>
                ))}
              </SelectField>
            )}
          </form.Field>
        )}

        <form.Field name="organization.address.street">
          {(field) => <BoundTextField field={field} label="Adresse" autoComplete="address-line1" />}
        </form.Field>

        <div className="grid gap-5 sm:grid-cols-[10rem_1fr]">
          <form.Field name="organization.address.postal_code">
            {(field) => (
              <BoundTextField
                field={field}
                label="Code postal"
                autoComplete="postal-code"
                inputMode="numeric"
              />
            )}
          </form.Field>
          <form.Field name="organization.address.city">
            {(field) => (
              <BoundTextField field={field} label="Ville" autoComplete="address-level2" />
            )}
          </form.Field>
        </div>

        <form.Field name="organization.contact_phone">
          {(field) => <BoundTextField field={field} label="Téléphone" type="tel" autoComplete="tel" />}
        </form.Field>
      </Section>

      <Section title="Votre compte">
        <div className="grid gap-5 sm:grid-cols-2">
          <form.Field name="account.firstname">
            {(field) => <BoundTextField field={field} label="Prénom" autoComplete="given-name" />}
          </form.Field>
          <form.Field name="account.lastname">
            {(field) => <BoundTextField field={field} label="Nom" autoComplete="family-name" />}
          </form.Field>
        </div>

        <form.Field name="account.email">
          {(field) => (
            <BoundTextField field={field} label="E-mail" type="email" autoComplete="email" />
          )}
        </form.Field>

        <form.Field name="account.password">
          {(field) => (
            <BoundTextField
              field={field}
              label="Mot de passe"
              type="password"
              autoComplete="new-password"
            />
          )}
        </form.Field>

        <form.Field name="account.password_confirmation">
          {(field) => (
            <BoundTextField
              field={field}
              label="Confirmation du mot de passe"
              type="password"
              autoComplete="new-password"
            />
          )}
        </form.Field>
      </Section>

      <div className="flex flex-col gap-5">
        {error && <FormAlert>{error}</FormAlert>}
        <form.Subscribe selector={(state) => state.isSubmitting}>
          {(isSubmitting) => (
            <SubmitButton pending={isSubmitting} pendingLabel="Envoi…">
              Envoyer ma demande
            </SubmitButton>
          )}
        </form.Subscribe>
      </div>
    </form>
  );
}
