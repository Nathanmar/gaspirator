import type { AnimationEvent, SyntheticEvent } from "react";

import { NAV_LINKS, STAGES } from "./content";
import { LogoMark } from "./logo-mark";

const RULER_TICKS = Array.from({ length: 41 }, (_, i) => i);

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

export function Hud() {
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

        <a
          href="#rejoindre"
          data-magnetic
          className="group rounded-full bg-lime px-5 py-2.5 font-mono text-[11px] font-semibold tracking-[0.18em] text-ink uppercase transition-colors duration-300 hover:bg-cream focus-visible:bg-cream"
        >
          {/* On hover the label rolls up and a copy takes its place from below. */}
          <span className="relative block overflow-hidden">
            <span className="relative block transition-transform duration-500 ease-[cubic-bezier(0.65,0,0.35,1)] group-hover:-translate-y-full group-focus-visible:-translate-y-full motion-reduce:transition-none">
              Rejoindre
              <span aria-hidden="true" className="absolute inset-x-0 top-full">
                Rejoindre
              </span>
            </span>
          </span>
        </a>
      </header>

      <aside
        data-hud
        aria-hidden="true"
        className="fixed top-1/2 right-5 z-40 hidden -translate-y-1/2 lg:block xl:right-10"
      >
        <div className="relative flex h-[46vh] gap-3">
          <div className="flex h-full flex-col justify-between">
            {RULER_TICKS.map((tick) => (
              <span
                key={tick}
                className={tick % 10 === 0 ? "h-px w-4 bg-cream/60" : "h-px w-2 bg-cream/25"}
              />
            ))}
          </div>
          <div className="flex h-full flex-col justify-between py-0 font-mono text-[10px] leading-none tracking-[0.15em] text-cream/45">
            {[100, 75, 50, 25, 0].map((value) => (
              <span key={value} className="-my-[0.3em]">
                {value}
              </span>
            ))}
          </div>
          <div data-ruler-marker className="absolute top-0 -left-3 flex items-center gap-2">
            <span className="block h-0.5 w-9 bg-lime" />
          </div>
        </div>
        <p className="mt-5 font-mono text-[10px] tracking-[0.2em] text-cream/45 uppercase">
          Gaspi
          <span data-ruler-value className="ml-2 inline-block w-[4ch] text-right text-lime">
            100%
          </span>
        </p>
      </aside>

      <div
        data-hud
        data-stage-hud
        aria-hidden="true"
        className="fixed right-5 bottom-5 z-40 flex items-center gap-3 font-mono text-[11px] tracking-[0.18em] text-cream/60 uppercase transition-[translate] duration-700 ease-out md:right-10 md:bottom-8"
      >
        <span>
          <span data-stage-index className="text-cream">
            00
          </span>
          <span className="text-cream/35"> / 0{STAGES.length - 1}</span>
        </span>
        <span className="h-px w-8 bg-cream/30" />
        <span data-stage-name>{STAGES[0].label}</span>
      </div>

      <div
        data-scroll-hint
        data-hidden
        aria-hidden="true"
        className="glass fixed bottom-5 left-1/2 z-40 hidden -translate-x-1/2 items-center gap-3 rounded-full py-2 pr-4 pl-2.5 font-mono text-[10px] tracking-[0.25em] text-cream/80 uppercase transition-opacity duration-500 md:bottom-8 md:flex"
      >
        <span className="relative flex h-6 w-4 justify-center rounded-full border border-cream/40">
          <span className="scroll-dot mt-1 size-1 rounded-full bg-lime" />
        </span>
        Scroll
      </div>
    </>
  );
}
