import { JoinButtons } from "../join-buttons";
import { SplitChars } from "../split-text";

// One centred column, read top to bottom: what it is, the name, the promise, then how.
export function HeroSection() {
  return (
    <section
      id="top"
      data-hero
      className="relative flex h-svh min-h-[600px] items-center justify-center px-5 pt-20 pb-16 md:px-10"
    >
      <div data-hero-inner className="flex max-w-4xl flex-col items-center text-center">
        <p
          data-hero-fade
          className="flex items-center gap-3 text-sm font-bold tracking-[0.14em] text-cream uppercase [text-shadow:0_0_6px_var(--color-ink),0_0_14px_var(--color-ink)] before:h-0.5 before:w-8 before:bg-lime after:h-0.5 after:w-8 after:bg-lime md:text-base"
        >
          Plateforme anti-gaspillage alimentaire
        </p>
        <h1 className="mt-4 font-display text-[min(18vw,22svh)] leading-[0.9] font-extrabold tracking-[-0.04em] whitespace-nowrap md:text-[min(13vw,22svh)]">
          <SplitChars text="Gaspirator" />
        </h1>
        <p
          data-hero-fade
          className="mt-6 text-3xl leading-tight font-semibold md:text-5xl"
        >
          Le surplus des uns, <span className="text-lime">le repas des autres.</span>
        </p>
        <p
          data-hero-fade
          className="mt-5 max-w-xl text-base leading-snug text-cream/70 md:text-lg"
        >
          Cantines, hôpitaux et supermarchés donnent leurs invendus aux associations proches,
          avant qu'ils ne finissent à la benne.
        </p>
        <JoinButtons data-hero-fade className="mt-8" />
      </div>
    </section>
  );
}
