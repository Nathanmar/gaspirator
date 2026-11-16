import { type ComponentProps, type ReactNode, useEffect, useRef, useState } from "react";

import { type AnyFieldApi, revalidateLogic, useForm, useStore } from "@tanstack/react-form";
import { ArrowLeft } from "lucide-react";

import {
  ChoiceField,
  FormAlert,
  SelectField,
  SubmitButton,
  TextField,
} from "@/components/form-controls";
import { cn } from "@/lib/utils";

import type { OrganizationType, RegistrationRequestCreate, SupplierType } from "./auth-api";
import {
  type RegisterFormValues,
  SUPPLIER_TYPES,
  accountSchema,
  organizationSchema,
  registerSchema,
} from "./register-schema";

type AccountValues = RegisterFormValues["account"];
type OrganizationValues = RegisterFormValues["organization"];

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
    account: { firstname: "", lastname: "", email: "", password: "", password_confirmation: "" },
    organization: {
      type,
      name: "",
      legal_id: "",
      supplier_type: "",
      address: { street: "", postal_code: "", city: "" },
      contact_phone: "",
    },
  };
}

function firstError(field: AnyFieldApi): string | undefined {
  return field.state.meta.errors[0]?.message;
}

/** Text input wired to a TanStack Form field. The id is prefixed with the step: `account-email`. */
function BoundTextField({
  field,
  idPrefix,
  ...props
}: { field: AnyFieldApi; idPrefix: string; label: string } & Omit<
  ComponentProps<typeof TextField>,
  "id" | "name" | "value" | "onChange" | "onBlur" | "error"
>) {
  return (
    <TextField
      id={`${idPrefix}-${field.name.replaceAll(".", "-")}`}
      name={field.name}
      value={field.state.value}
      onBlur={field.handleBlur}
      onChange={(e) => field.handleChange(e.target.value)}
      error={firstError(field)}
      {...props}
    />
  );
}

/** Progress bar, step number and title of a step. */
function StepHeader({ step, title, focus }: { step: 1 | 2; title: string; focus: boolean }) {
  const titleRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    // After a step change, bring the new step into view and have it announced.
    if (focus) titleRef.current?.focus();
  }, [focus]);

  return (
    <div className="flex flex-col gap-3">
      <div aria-hidden="true" className="grid grid-cols-2 gap-2">
        <span className="h-1 rounded-full bg-lime" />
        <span className={cn("h-1 rounded-full", step === 2 ? "bg-lime" : "bg-cream/15")} />
      </div>
      <p className="text-xs font-semibold tracking-[0.14em] text-cream/60 uppercase">
        {`Étape ${step} sur 2`}
      </p>
      <h2
        ref={titleRef}
        tabIndex={-1}
        className="text-2xl font-extrabold tracking-[-0.03em] outline-none"
      >
        {title}
      </h2>
    </div>
  );
}

function StepForm({ onSubmit, children }: { onSubmit: () => Promise<void>; children: ReactNode }) {
  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={(e) => {
        e.preventDefault();
        void onSubmit();
      }}
    >
      {children}
    </form>
  );
}

type AccountStepProps = {
  defaultValues: AccountValues;
  focusTitle: boolean;
  onContinue: (account: AccountValues) => void;
};

/** Step 1: the account of the organization's manager. */
function AccountStep({ defaultValues, focusTitle, onContinue }: AccountStepProps) {
  const form = useForm({
    defaultValues,
    // Validate on submit first, then on every change so an error goes away as soon as it is fixed.
    validationLogic: revalidateLogic(),
    validators: { onDynamic: accountSchema },
    // Raw values are kept (not the parsed ones) so they show unchanged when coming back.
    onSubmit: ({ value }) => onContinue(value),
  });

  return (
    <StepForm onSubmit={form.handleSubmit}>
      <StepHeader step={1} title="Votre compte" focus={focusTitle} />

      <div className="grid gap-5 sm:grid-cols-2">
        <form.Field name="firstname">
          {(field) => (
            <BoundTextField field={field} idPrefix="account" label="Prénom" autoComplete="given-name" />
          )}
        </form.Field>
        <form.Field name="lastname">
          {(field) => (
            <BoundTextField field={field} idPrefix="account" label="Nom" autoComplete="family-name" />
          )}
        </form.Field>
      </div>

      <form.Field name="email">
        {(field) => (
          <BoundTextField
            field={field}
            idPrefix="account"
            label="E-mail"
            type="email"
            autoComplete="email"
          />
        )}
      </form.Field>

      <form.Field name="password">
        {(field) => (
          <BoundTextField
            field={field}
            idPrefix="account"
            label="Mot de passe"
            type="password"
            autoComplete="new-password"
          />
        )}
      </form.Field>

      <form.Field name="password_confirmation">
        {(field) => (
          <BoundTextField
            field={field}
            idPrefix="account"
            label="Confirmation du mot de passe"
            type="password"
            autoComplete="new-password"
          />
        )}
      </form.Field>

      {/* An intermediate step: a shorter button than the final "Envoyer ma demande", on the right
          like a "next" action. */}
      <div className="mt-3 flex justify-end">
        <SubmitButton className="w-auto min-w-52">Continuer</SubmitButton>
      </div>
    </StepForm>
  );
}

type OrganizationStepProps = {
  defaultValues: OrganizationValues;
  focusTitle: boolean;
  error?: string | null;
  // Receives the current values so they are kept when coming back to this step.
  onBack: (organization: OrganizationValues) => void;
  onSubmit: (organization: OrganizationValues) => void | Promise<void>;
};

/** Step 2: the organization, then the request is sent. */
function OrganizationStep({
  defaultValues,
  focusTitle,
  error,
  onBack,
  onSubmit,
}: OrganizationStepProps) {
  const form = useForm({
    defaultValues,
    validationLogic: revalidateLogic(),
    validators: { onDynamic: organizationSchema },
    onSubmit: ({ value }) => onSubmit(value),
  });
  // The legal ID label and the establishment type depend on the organization type.
  const type = useStore(form.store, (state) => state.values.type);

  return (
    <StepForm onSubmit={form.handleSubmit}>
      <StepHeader step={2} title="Votre organisation" focus={focusTitle} />

      <form.Field name="type">
        {(field) => (
          <ChoiceField
            name="organization-type"
            legend="Type d'organisation"
            options={ORGANIZATION_TYPES}
            value={field.state.value}
            onChange={(value) => field.handleChange(value)}
            onBlur={field.handleBlur}
            error={firstError(field)}
          />
        )}
      </form.Field>

      <form.Field name="name">
        {(field) => (
          <BoundTextField
            field={field}
            idPrefix="organization"
            label="Nom de l'organisation"
            autoComplete="organization"
          />
        )}
      </form.Field>

      <form.Field name="legal_id">
        {(field) => (
          <BoundTextField
            field={field}
            idPrefix="organization"
            label={LEGAL_ID_LABELS[type]}
            autoComplete="off"
            // A SIRET is only digits: show the numeric keypad on mobile.
            inputMode={type === "supplier" ? "numeric" : "text"}
            placeholder={type === "association" ? "W123456789" : undefined}
          />
        )}
      </form.Field>

      {type === "supplier" && (
        <form.Field name="supplier_type">
          {(field) => (
            <SelectField
              id="organization-supplier_type"
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

      <form.Field name="address.street">
        {(field) => (
          <BoundTextField
            field={field}
            idPrefix="organization"
            label="Adresse"
            autoComplete="address-line1"
          />
        )}
      </form.Field>

      <div className="grid gap-5 sm:grid-cols-[10rem_1fr]">
        <form.Field name="address.postal_code">
          {(field) => (
            <BoundTextField
              field={field}
              idPrefix="organization"
              label="Code postal"
              autoComplete="postal-code"
              inputMode="numeric"
            />
          )}
        </form.Field>
        <form.Field name="address.city">
          {(field) => (
            <BoundTextField
              field={field}
              idPrefix="organization"
              label="Ville"
              autoComplete="address-level2"
            />
          )}
        </form.Field>
      </div>

      <form.Field name="contact_phone">
        {(field) => (
          <BoundTextField
            field={field}
            idPrefix="organization"
            label="Téléphone"
            type="tel"
            autoComplete="tel"
          />
        )}
      </form.Field>

      {/* The error sits next to the submit button, where the user is looking. */}
      <div className="mt-3 flex flex-col gap-3">
        {error && <FormAlert>{error}</FormAlert>}
        <form.Subscribe selector={(state) => state.isSubmitting}>
          {(isSubmitting) => (
            <>
              <SubmitButton pending={isSubmitting} pendingLabel="Envoi…">
                Envoyer ma demande
              </SubmitButton>
              <button
                type="button"
                disabled={isSubmitting}
                onClick={() => onBack(form.state.values)}
                className="inline-flex h-12 items-center justify-center gap-2 self-center rounded-full px-5 text-sm font-semibold text-cream/70 transition-colors hover:text-cream disabled:opacity-50"
              >
                <ArrowLeft aria-hidden="true" className="size-4" />
                Retour
              </button>
            </>
          )}
        </form.Subscribe>
      </div>
    </StepForm>
  );
}

type RegisterFormProps = {
  // Organization type chosen on the landing page, preselected in step 2.
  defaultType?: OrganizationType;
  // Error of the whole request, shown in step 2 next to the submit button.
  error?: string | null;
  // While the returned promise is pending, the submit button is disabled.
  onSubmit: (request: RegistrationRequestCreate) => void | Promise<void>;
};

/**
 * Registration in two steps: the manager's account, then the organization. Each step is its own
 * form with its own schema, so "Continuer" only checks the account. The values of both steps live
 * here, so going back and forth loses nothing.
 */
export function RegisterForm({ defaultType, error, onSubmit }: RegisterFormProps) {
  const [values, setValues] = useState<RegisterFormValues>(() => emptyValues(defaultType ?? ""));
  const [step, setStep] = useState<"account" | "organization">("account");
  // The focus only moves after a step change, not when the page first shows.
  const [hasChangedStep, setHasChangedStep] = useState(false);

  function goTo(nextStep: "account" | "organization", nextValues: RegisterFormValues) {
    setValues(nextValues);
    setStep(nextStep);
    setHasChangedStep(true);
  }

  if (step === "account") {
    return (
      <AccountStep
        defaultValues={values.account}
        focusTitle={hasChangedStep}
        onContinue={(account) => goTo("organization", { ...values, account })}
      />
    );
  }

  return (
    <OrganizationStep
      defaultValues={values.organization}
      focusTitle={hasChangedStep}
      error={error}
      onBack={(organization) => goTo("account", { ...values, organization })}
      // The full schema output is the request body of the contract (without the confirmation).
      onSubmit={(organization) => onSubmit(registerSchema.parse({ ...values, organization }))}
    />
  );
}
