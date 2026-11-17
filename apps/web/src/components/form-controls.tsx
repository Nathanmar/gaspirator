import type { ComponentProps, ReactNode } from "react";

import { Select as SelectPrimitive } from "@base-ui/react/select";
import { ArrowUpRight, Check, ChevronDown, CircleAlert, LoaderCircle } from "lucide-react";

import { cn } from "@/lib/utils";

// Form controls in the landing page's visual identity. Mobile first: 48px tall touch targets and a
// 16px font size, below which iOS zooms in on the focused field.

const labelClass = "text-xs font-semibold tracking-[0.14em] text-cream/70 uppercase";

const controlClass =
  "h-12 w-full rounded-2xl border border-cream/15 bg-white/70 px-4 text-base text-cream outline-none transition-colors placeholder:text-cream/40 focus-visible:border-lime focus-visible:ring-2 focus-visible:ring-lime/30 aria-invalid:border-tomato aria-invalid:ring-2 aria-invalid:ring-tomato/20";

/** Main call to action: lime pill with a round arrow, like the landing page buttons. */
export const primaryButtonClass =
  "group inline-flex h-14 w-full items-center justify-between gap-4 rounded-full bg-lime py-2 pr-2 pl-6 text-xs font-semibold tracking-[0.18em] text-ink uppercase transition-opacity disabled:cursor-wait disabled:opacity-70";

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

function LabelledField({ id, label, error, children }: FieldProps & { children: ReactNode }) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      {children}
      <FieldError id={id} error={error} />
    </div>
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
    <LabelledField id={id} label={label} error={error}>
      <input
        id={id}
        className={cn(controlClass, className)}
        {...errorAttributes(id, error)}
        {...props}
      />
    </LabelledField>
  );
}

/** Select in the landing style (Base UI). An empty string means nothing is chosen yet. */
export function SelectField<T extends string>({
  id,
  label,
  error,
  name,
  options,
  value,
  placeholder,
  onChange,
  onBlur,
}: FieldProps & {
  name: string;
  options: readonly { value: T; label: string }[];
  value: T | "";
  placeholder: string;
  onChange: (value: T) => void;
  onBlur: () => void;
}) {
  return (
    <LabelledField id={id} label={label} error={error}>
      <SelectPrimitive.Root
        name={name}
        items={options}
        value={value === "" ? null : value}
        onValueChange={(next) => next !== null && onChange(next)}
      >
        <SelectPrimitive.Trigger
          id={id}
          onBlur={onBlur}
          className={cn(controlClass, "flex items-center justify-between gap-2 text-left")}
          {...errorAttributes(id, error)}
        >
          <SelectPrimitive.Value
            placeholder={placeholder}
            className="truncate data-placeholder:text-cream/40"
          />
          <SelectPrimitive.Icon>
            <ChevronDown aria-hidden="true" className="size-4 text-cream/60" />
          </SelectPrimitive.Icon>
        </SelectPrimitive.Trigger>
        <SelectPrimitive.Portal>
          {/* `landing` brings the colour tokens into the portal, outside the page's wrapper. */}
          <SelectPrimitive.Positioner
            sideOffset={6}
            alignItemWithTrigger={false}
            className="landing z-50 outline-none"
          >
            <SelectPrimitive.Popup className="max-h-(--available-height) w-(--anchor-width) overflow-y-auto rounded-2xl border border-cream/15 bg-white p-1.5 font-display text-cream shadow-lg outline-none">
              {options.map((option) => (
                <SelectPrimitive.Item
                  key={option.value}
                  value={option.value}
                  className="flex h-11 cursor-pointer items-center justify-between gap-2 rounded-xl px-3 text-base outline-none select-none data-highlighted:bg-lime/15"
                >
                  <SelectPrimitive.ItemText>{option.label}</SelectPrimitive.ItemText>
                  <SelectPrimitive.ItemIndicator>
                    <Check aria-hidden="true" className="size-4 text-lime" />
                  </SelectPrimitive.ItemIndicator>
                </SelectPrimitive.Item>
              ))}
            </SelectPrimitive.Popup>
          </SelectPrimitive.Positioner>
        </SelectPrimitive.Portal>
      </SelectPrimitive.Root>
    </LabelledField>
  );
}

type ChoiceOption<T extends string> = { value: T; label: string; tone: "lime" | "tomato" };

/**
 * Radio buttons shown as pills, one per option, filled with the option's colour when checked.
 * The real radio inputs stay in the page (visually hidden) for keyboards and screen readers.
 */
export function ChoiceField<T extends string>({
  name,
  legend,
  options,
  value,
  onChange,
  onBlur,
  error,
}: {
  name: string;
  legend: string;
  options: readonly ChoiceOption<T>[];
  value: string;
  onChange: (value: T) => void;
  onBlur: () => void;
  error?: string;
}) {
  return (
    <fieldset aria-describedby={error ? errorId(name) : undefined}>
      <legend className={labelClass}>{legend}</legend>
      <div className="mt-2 grid grid-cols-2 gap-2">
        {options.map((option) => (
          <label
            key={option.value}
            className={cn(
              "flex h-12 cursor-pointer items-center justify-center rounded-full border border-cream/15 bg-white/70 px-4 text-sm font-semibold transition-colors has-checked:text-ink has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-lime/40",
              option.tone === "lime"
                ? "has-checked:border-lime has-checked:bg-lime"
                : "has-checked:border-tomato has-checked:bg-tomato",
            )}
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              onBlur={onBlur}
              className="sr-only"
            />
            {option.label}
          </label>
        ))}
      </div>
      <div className="mt-2">
        <FieldError id={name} error={error} />
      </div>
    </fieldset>
  );
}

export function SubmitButton({
  pending = false,
  pendingLabel,
  className,
  children,
}: {
  pending?: boolean;
  // Replaces the label while the request is running, e.g. "Connexion…".
  pendingLabel?: string;
  // Full width by default; overrides such as a shorter width go here.
  className?: string;
  children: ReactNode;
}) {
  return (
    <button type="submit" disabled={pending} className={cn(primaryButtonClass, className)}>
      {pending && pendingLabel ? pendingLabel : children}
      <ArrowBadge pending={pending} />
    </button>
  );
}

/** Round arrow at the end of a primary button or link; it turns on hover, spins while pending. */
export function ArrowBadge({ pending = false }: { pending?: boolean }) {
  return (
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
  );
}

/**
 * Error of the whole form (wrong credentials, server unreachable…), announced when it appears.
 * The content may hold a list, hence a `div` rather than a paragraph.
 */
export function FormAlert({ children }: { children: ReactNode }) {
  return (
    <div
      role="alert"
      className="flex gap-3 rounded-2xl border border-tomato/30 bg-tomato/10 px-4 py-3 text-sm leading-snug font-medium text-cream"
    >
      <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-tomato" />
      <div>{children}</div>
    </div>
  );
}
