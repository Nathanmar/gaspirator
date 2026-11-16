import type { ReactNode, Ref } from "react";

import { Link } from "@tanstack/react-router";

import { LogoMark } from "@/components/landing/logo-mark";
import { cn } from "@/lib/utils";

type AuthLayoutProps = {
  // Small lime line above the title, as on the landing page.
  eyebrow: string;
  title: string;
  // Lets a page move the focus to the title, e.g. when a confirmation replaces a long form.
  titleRef?: Ref<HTMLHeadingElement>;
  description?: ReactNode;
  // Under the card: link to the other auth page, styled here.
  footer?: ReactNode;
  // The registration form needs more room than the login form.
  wide?: boolean;
  children: ReactNode;
};

/**
 * Shell of the login and registration pages, in the landing page's visual identity: the `landing`
 * class brings its colour tokens (paper background, lime and tomato accents), plus its glow,
 * glass card and grain. One column on mobile; the content is centred on larger screens.
 */
export function AuthLayout({
  eyebrow,
  title,
  titleRef,
  description,
  footer,
  wide,
  children,
}: AuthLayoutProps) {
  return (
    <div className="landing relative isolate flex min-h-svh flex-col bg-ink font-display text-cream">
      <div aria-hidden="true" className="landing-glow pointer-events-none fixed inset-0 -z-10" />

      <header className="px-5 py-4 md:px-10 md:py-6">
        <Link
          to="/"
          className="inline-flex items-center gap-2.5"
          aria-label="Gaspirator, retour à l'accueil"
        >
          <LogoMark className="h-9 w-auto" />
          <span className="text-xl font-bold tracking-[-0.03em]">gaspirator</span>
        </Link>
      </header>

      <main className="flex flex-1 justify-center px-5 pt-6 pb-16 md:items-center md:px-10">
        <div className={cn("w-full", wide ? "max-w-2xl" : "max-w-md")}>
          <p className="text-sm font-semibold tracking-[0.12em] text-lime uppercase">{eyebrow}</p>
          <h1
            ref={titleRef}
            tabIndex={-1}
            className="mt-3 text-5xl leading-[0.95] font-extrabold tracking-[-0.04em] outline-none md:text-6xl"
          >
            {title}
          </h1>
          {description && (
            <p className="mt-4 text-base leading-snug text-cream/70 md:text-lg">{description}</p>
          )}

          <div className="glass mt-8 rounded-[28px] p-5 sm:p-8">{children}</div>

          {footer && (
            <p className="mt-6 text-center text-sm text-cream/70 [&_a]:font-semibold [&_a]:text-cream [&_a]:underline [&_a]:underline-offset-4">
              {footer}
            </p>
          )}
        </div>
      </main>

      <div aria-hidden="true" className="grain" />
    </div>
  );
}
