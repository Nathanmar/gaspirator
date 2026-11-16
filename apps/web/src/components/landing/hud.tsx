import type { AnimationEvent, ReactNode, SyntheticEvent } from "react";

import { Link } from "@tanstack/react-router";

import { useAuthStore } from "@/features/auth/auth-store";
import { useLogout } from "@/features/auth/use-logout";

import { NAV_LINKS } from "./content";
import { LogoMark } from "./logo-mark";

// The logo makes one quick turn each time the link is hovered or focused. A spin already under
// way runs to its end rather than restarting, so the mark never jumps.
function startSpin(event: SyntheticEvent<HTMLAnchorElement>) {
  event.currentTarget.querySelector("svg")?.classList.add("logo-tornado");
}

function endSpin(event: AnimationEvent<HTMLAnchorElement>) {
  const svg = event.currentTarget.querySelector("svg");
  // Wait for the last band, which starts latest.
  if (svg && svg.getAnimations({ subtree: true }).length === 0) {
    svg.classList.remove("logo-tornado");
  }
}

const pillClass =
  "group rounded-full bg-lime px-5 py-2.5 font-mono text-[11px] font-semibold tracking-[0.18em] text-ink uppercase transition-colors duration-300 hover:bg-cream focus-visible:bg-cream";

// On hover the label rolls up and a copy takes its place from below.
function RollingLabel({ children }: { children: ReactNode }) {
  return (
    <span className="relative block overflow-hidden">
      <span className="relative block transition-transform duration-500 ease-[cubic-bezier(0.65,0,0.35,1)] group-hover:-translate-y-full group-focus-visible:-translate-y-full motion-reduce:transition-none">
        {children}
        <span aria-hidden="true" className="absolute inset-x-0 top-full">
          {children}
        </span>
      </span>
    </span>
  );
}

export function Hud() {
  // Logged in: the join button gives way to the logout button.
  const isLoggedIn = useAuthStore((state) => state.tokens !== null);
  const logOut = useLogout();

  return (
    <>
      <header
        data-hud
        className="fixed inset-x-0 top-0 z-40 flex items-center justify-between bg-linear-to-b from-ink/80 to-transparent px-5 py-4 md:px-10 md:py-6"
      >
        <a
          href="#top"
          className="flex items-center gap-2.5"
          aria-label="Gaspirator, retour en haut"
          onMouseEnter={startSpin}
          onFocus={startSpin}
          onAnimationEnd={endSpin}
        >
          <LogoMark className="h-9 w-auto" />
          <span className="font-display text-xl font-bold tracking-[-0.03em]">gaspirator</span>
        </a>

        <nav aria-label="Sections" className="glass hidden rounded-full p-1 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="rounded-full px-4 py-2 font-mono text-[11px] tracking-[0.18em] text-cream/75 uppercase transition-colors hover:bg-cream/10 hover:text-cream"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {isLoggedIn ? (
          <button type="button" data-magnetic className={pillClass} onClick={() => void logOut()}>
            <RollingLabel>Se déconnecter</RollingLabel>
          </button>
        ) : (
          <Link to="/register" data-magnetic className={pillClass}>
            <RollingLabel>Rejoindre</RollingLabel>
          </Link>
        )}
      </header>
    </>
  );
}
