import { revalidateLogic, useForm } from "@tanstack/react-form";

import { SubmitButton, TextField } from "@/components/form-controls";

import { type LoginFormValues, loginSchema } from "./login-schema";

const FIELDS = [
  { name: "email", label: "E-mail", type: "email", autoComplete: "email" },
  { name: "password", label: "Mot de passe", type: "password", autoComplete: "current-password" },
] as const;

type LoginFormProps = {
  // While the returned promise is pending, the submit button is disabled.
  onSubmit: (values: LoginFormValues) => void | Promise<void>;
};

export function LoginForm({ onSubmit }: LoginFormProps) {
  const form = useForm({
    defaultValues: { email: "", password: "" },
    // Validate on submit first, then on every change so an error goes away as soon as it is fixed.
    validationLogic: revalidateLogic(),
    validators: { onDynamic: loginSchema },
    // Parse again so the submitted email is trimmed, as the schema defines.
    onSubmit: ({ value }) => onSubmit(loginSchema.parse(value)),
  });

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={(e) => {
        e.preventDefault();
        void form.handleSubmit();
      }}
    >
      {FIELDS.map(({ name, ...input }) => (
        <form.Field key={name} name={name}>
          {(field) => (
            <TextField
              id={name}
              name={name}
              {...input}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(e) => field.handleChange(e.target.value)}
              error={field.state.meta.errors[0]?.message}
            />
          )}
        </form.Field>
      ))}

      <form.Subscribe selector={(state) => state.isSubmitting}>
        {(isSubmitting) => (
          <SubmitButton pending={isSubmitting} pendingLabel="Connexion…">
            Se connecter
          </SubmitButton>
        )}
      </form.Subscribe>
    </form>
  );
}
