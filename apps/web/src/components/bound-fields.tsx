import type { ComponentProps } from "react";

import type { AnyFieldApi } from "@tanstack/react-form";

import { TextField } from "./form-controls";

// Form controls wired to TanStack Form fields. `AnyFieldApi` is TanStack's type for "any field":
// it keeps these helpers short, at the cost of typing the field value as `any` inside them.

/** First validation error of a field, as shown under its control. */
export function firstError(field: AnyFieldApi): string | undefined {
  return field.state.meta.errors[0]?.message;
}

/**
 * TextField bound to a field: value, change, blur and error. Its id is the field name, prefixed
 * when given (`account` + `email` -> `account-email`), with dots turned into dashes.
 */
export function BoundTextField({
  field,
  idPrefix,
  ...props
}: { field: AnyFieldApi; idPrefix?: string; label: string } & Omit<
  ComponentProps<typeof TextField>,
  "id" | "name" | "value" | "onChange" | "onBlur" | "error"
>) {
  const id = field.name.replaceAll(".", "-");

  return (
    <TextField
      id={idPrefix ? `${idPrefix}-${id}` : id}
      name={field.name}
      value={field.state.value}
      onBlur={field.handleBlur}
      onChange={(e) => field.handleChange(e.target.value)}
      error={firstError(field)}
      {...props}
    />
  );
}
