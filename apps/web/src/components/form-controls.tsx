import type { ComponentProps, ReactNode } from "react";

import { ArrowUpRight, CircleAlert, LoaderCircle } from "lucide-react";

import { cn } from "@/lib/utils";

// Form controls in the landing page's visual identity. Mobile first: 48px tall touch targets and a
// 16px font size, below which iOS zooms in on the focused field.

const labelClass = "text-xs font-semibold tracking-[0.14em] text-cream/70 uppercase";

const controlClass =
  "h-12 w-full rounded-2xl border border-cream/15 bg-white/70 px-4 text-base text-cream outline-none transition-colors placeholder:text-cream/40 focus-visible:border-lime focus-visible:ring-2 focus-visible:ring-lime/30 aria-invalid:border-tomato aria-invalid:ring-2 aria-invalid:ring-tomato/20";

type FieldProps = {
  id: string;
  label: string;
  // First validation error of the field, shown under it and announced with it.
  error?: string;
};

function errorId(id: string) {
  return `${id}-error`;
}

// Links the control to its error so screen readers read both.
function errorAttributes(id: string, error?: string) {
  return error ? { "aria-invalid": true, "aria-describedby": errorId(id) } : {};
}

function FieldError({ id, error }: { id: string; error?: string }) {
  if (!error) return null;
  return (
    <p id={errorId(id)} className="text-sm font-medium text-tomato">
      {error}
    </p>
  );
}

export function TextField({
  id,
  label,
  error,
  className,
  ...props
}: FieldProps & Omit<ComponentProps<"input">, "id">) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      <input
        id={id}
        className={cn(controlClass, className)}
        {...errorAttributes(id, error)}
        {...props}
      />
      <FieldError id={id} error={error} />
    </div>
  );
}

export function SubmitButton({
  pending,
  pendingLabel,
  children,
}: {
  pending: boolean;
  // Replaces the label while the request is running, e.g. "Connexion…".
  pendingLabel: string;
  children: ReactNode;
}) {
  return (
    <button
      type="submit"
      disabled={pending}
      className="group inline-flex h-14 w-full items-center justify-between gap-4 rounded-full bg-lime py-2 pr-2 pl-6 text-xs font-semibold tracking-[0.18em] text-ink uppercase transition-opacity disabled:cursor-wait disabled:opacity-70"
    >
      {pending ? pendingLabel : children}
      <span
        aria-hidden="true"
        className="grid size-10 place-items-center rounded-full bg-ink text-cream transition-transform duration-300 group-hover:rotate-45 group-disabled:rotate-0"
      >
        {pending ? (
          <LoaderCircle className="size-4 animate-spin" />
        ) : (
          <ArrowUpRight className="size-4" />
        )}
      </span>
    </button>
  );
}

/** Error of the whole form (wrong credentials, server unreachable…), announced when it appears. */
export function FormAlert({ children }: { children: ReactNode }) {
  return (
    <p
      role="alert"
      className="flex gap-3 rounded-2xl border border-tomato/30 bg-tomato/10 px-4 py-3 text-sm leading-snug font-medium text-cream"
    >
      <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-tomato" />
      {children}
    </p>
  );
}
