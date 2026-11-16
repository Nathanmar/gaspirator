import { SplitChars } from "../split-text";

export function HeroSection() {
  return (
    <section
      id="top"
      data-hero
      className="relative flex h-svh min-h-[600px] flex-col justify-between px-5 pt-24 pb-16 md:px-10 md:pt-28 md:pb-20 lg:pr-32 xl:pr-36"
    >
      <div className="flex items-start justify-between gap-6 font-mono text-[11px] tracking-[0.2em] text-cream/60 uppercase">
        <p data-hero-fade>
          Plateforme
          <br />
          anti-gaspillage alimentaire
        </p>
      </div>

      <div data-hero-inner>
        <div className="mb-5 flex flex-col-reverse gap-5 md:mb-4 md:flex-row md:items-end md:justify-between">
          <p data-hero-fade className="max-w-sm text-base leading-snug text-cream/70 md:text-lg">
            Cantines, hôpitaux et supermarchés donnent leurs invendus aux associations proches,
            avant qu'ils ne finissent à la benne.
          </p>
          <p data-hero-fade className="font-serif text-4xl leading-[0.95] italic md:text-6xl">
            Le surplus des uns,
            <br />
            <span className="text-lime">le repas des autres.</span>
          </p>
        </div>
        <h1 className="-mx-[0.02em] font-display text-[min(30.5vw,42svh)] leading-[0.78] lg:text-[min(calc((100vw-10.5rem)/2.95),42svh)] xl:text-[min(calc((100vw-11.5rem)/2.95),42svh)] font-extrabold tracking-[-0.055em] whitespace-nowrap [font-stretch:75%]">
          <SplitChars text="Gaspirator" />
        </h1>
      </div>
    </section>
  );
}
