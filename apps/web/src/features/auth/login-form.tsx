import type { z } from "zod";

import { useForm } from "@tanstack/react-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { loginSchema } from "./login-schema";

type LoginValues = z.output<typeof loginSchema>;

export function LoginForm({ onSubmit }: { onSubmit: (values: LoginValues) => void }) {
  const form = useForm({
    defaultValues: { email: "", password: "" },
    validators: { onSubmit: loginSchema },
    // Parse again so the submitted email is trimmed, as the schema defines.
    onSubmit: ({ value }) => onSubmit(loginSchema.parse(value)),
  });

  return (
    <form
      noValidate
      className="flex flex-col gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        void form.handleSubmit();
      }}
    >
      {(
        [
          { name: "email", label: "E-mail", type: "email", autoComplete: "email" },
          { name: "password", label: "Mot de passe", type: "password", autoComplete: "current-password" },
        ] as const
      ).map(({ name, label, type, autoComplete }) => (
        <form.Field key={name} name={name}>
          {(field) => {
            const error = field.state.meta.errors[0]?.message;
            const errorId = `${name}-error`;
            return (
              <div className="flex flex-col gap-1.5">
                <Label htmlFor={name}>{label}</Label>
                <Input
                  id={name}
                  name={name}
                  type={type}
                  autoComplete={autoComplete}
                  value={field.state.value}
                  onBlur={field.handleBlur}
                  onChange={(e) => field.handleChange(e.target.value)}
                  aria-invalid={error ? true : undefined}
                  aria-describedby={error ? errorId : undefined}
                />
                {error && (
                  <p id={errorId} className="text-xs text-destructive">
                    {error}
                  </p>
                )}
              </div>
            );
          }}
        </form.Field>
      ))}
      <Button type="submit">Se connecter</Button>
    </form>
  );
}
