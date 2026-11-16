import { SectionLabel } from "../section-label";

export function ProblemSection() {
  return (
    <section
      id="constat"
      data-stage
      className="relative px-5 pt-[24vh] pb-[30vh] md:px-10 lg:pr-32 xl:pr-36"
    >
      <SectionLabel index="01" title="Le constat" />

      {/* Each figure sits right next to its caption (fixed gap, capped width) so that on wide
          screens a caption can't be read as belonging to the other figure. */}
      <div className="mt-12 flex flex-col gap-6 md:flex-row md:items-end md:gap-10">
        <p
          data-reveal
          className="shrink-0 font-display text-[44vw] leading-[0.78] font-extrabold tracking-[-0.06em] [font-stretch:75%] md:text-[27vw]"
        >
          1<span className="font-serif font-normal text-tomato italic">/</span>3
        </p>
        <div data-reveal className="max-w-xs md:max-w-[22rem] md:pb-[1.5vw]">
          <p className="text-2xl leading-tight md:text-[min(2.1vw,2.25rem)]">
            de la nourriture produite dans le monde est perdue ou gaspillée.
          </p>
          <p className="mt-4 font-mono text-[10px] tracking-[0.2em] text-cream/45 uppercase">
            Source — FAO, 2011
          </p>
        </div>
      </div>

      <div className="mt-[22vh] flex flex-col gap-6 md:mt-[30vh] md:flex-row-reverse md:items-end md:gap-10">
        <p
          data-reveal
          className="shrink-0 font-display text-[34vw] leading-[0.8] font-extrabold tracking-[-0.06em] [font-stretch:75%] md:text-[22vw]"
        >
          <span data-count-to="10">10</span>
          <span className="ml-[0.08em] font-serif text-[0.5em] font-normal tracking-normal italic">
            Mt
          </span>
        </p>
        <div data-reveal className="max-w-xs md:max-w-[22rem] md:pb-[1.5vw] md:text-right">
          <p className="text-2xl leading-tight md:text-[min(2.1vw,2.25rem)]">
            de nourriture perdue ou gaspillée chaque année, rien qu'en France.
          </p>
          <p className="mt-4 font-mono text-[10px] tracking-[0.2em] text-cream/45 uppercase">
            Source — ADEME, 2016
          </p>
        </div>
      </div>

      <p
        data-reveal
        className="mx-auto mt-[26vh] max-w-4xl text-center font-serif text-4xl leading-[1.02] italic md:text-7xl"
      >
        Pendant ce temps, à quelques rues de là, des associations cherchent de quoi{" "}
        <span className="text-lime">remplir leurs étagères.</span>
      </p>
    </section>
  );
}
