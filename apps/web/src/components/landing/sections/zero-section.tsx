import { ArrowUpRight } from "lucide-react";

import { cn } from "@/lib/utils";

import { JOIN_LINKS } from "../content";
import { LogoMark } from "../logo-mark";
import { SectionLabel } from "../section-label";

const MARQUEE = "Rien ne se perd — tout se donne — ";

export function ZeroSection() {
  return (
    <section id="rejoindre" data-stage data-zero className="relative flex min-h-svh flex-col">
      <div className="flex min-h-svh flex-col items-center justify-center px-5 py-28 text-center">
        <SectionLabel index="05" title="Objectif" className="mb-6" />
        <h2 className="relative">
          <span
            data-zero-top
            className="block font-display text-[16vw] leading-[0.82] font-extrabold tracking-[-0.05em] [font-stretch:75%] md:text-[9vw]"
          >
            Objectif
          </span>
          <span
            data-zero-word
            className="block font-serif text-[38vw] leading-[0.72] text-lime italic md:text-[22vw]"
          >
            zéro
          </span>
          <span className="sr-only">gaspillage</span>
        </h2>
        <p data-reveal className="mt-8 max-w-md text-lg leading-snug text-cream/70">
          Chaque don publié, c'est un repas de plus servi, et un déchet de moins.
        </p>
        <div data-reveal className="mt-10 flex flex-col gap-3 sm:flex-row">
          {JOIN_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              data-magnetic
              className={cn(
                "group inline-flex items-center justify-between gap-4 rounded-full py-2 pr-2 pl-6 font-mono text-[11px] font-semibold tracking-[0.18em] text-ink uppercase",
                link.tone === "lime" ? "bg-lime" : "bg-tomato",
              )}
            >
              {link.label}
              <span className="grid size-9 place-items-center rounded-full bg-ink text-cream transition-transform duration-300 group-hover:rotate-45">
                <ArrowUpRight className="size-4" />
              </span>
            </a>
          ))}
        </div>
      </div>

      <footer className="relative border-t border-cream/10 bg-ink/40 backdrop-blur-sm">
        <div className="hud-clear overflow-hidden py-6 md:py-10" aria-hidden="true">
          <div data-marquee className="flex w-max will-change-transform">
            {[0, 1].map((copy) => (
              <span
                key={copy}
                className="text-outline pr-[0.3em] font-display text-[18vw] leading-none font-extrabold whitespace-nowrap uppercase [font-stretch:75%] md:text-[11vw]"
              >
                {MARQUEE.repeat(2)}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-4 border-t border-cream/10 px-5 py-6 font-mono text-[11px] tracking-[0.18em] text-cream/50 uppercase md:flex-row md:items-center md:justify-between md:px-10">
          <span className="flex items-center gap-2 text-cream">
            <LogoMark className="h-6 w-auto" />
            Gaspirator © {new Date().getFullYear()}
          </span>
          <a href="#top" className="transition-colors hover:text-lime">
            Retour en haut ↑
          </a>
        </div>
      </footer>
    </section>
  );
}
