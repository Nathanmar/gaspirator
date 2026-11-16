
export function ProblemSection() {
  return (
    <section
      id="constat"
      data-stage
      className="relative px-5 pb-[30vh] md:px-10"
    >
      {/* Both figures side by side (stacked on mobile), centred on one screen. */}
      <div className="mx-auto grid min-h-svh max-w-6xl content-center gap-12 py-24 text-center md:grid-cols-2 md:gap-10">
        <div data-reveal>
          <p className="font-display text-[28vw] leading-[0.85] font-extrabold tracking-[-0.05em] md:text-[min(15vw,30svh)]">
            1<span className="text-tomato">/</span>3
          </p>
          <p className="mx-auto mt-4 max-w-sm text-xl leading-tight md:text-2xl">
            de la nourriture produite dans le monde est perdue ou gaspillée.
          </p>
          <p className="mt-3 font-mono text-xs tracking-[0.15em] text-cream/55 uppercase">
            Source — FAO, 2011
          </p>
        </div>

        <div data-reveal>
          <p className="font-display text-[28vw] leading-[0.85] font-extrabold tracking-[-0.05em] md:text-[min(15vw,30svh)]">
            <span data-count-to="10">10</span>
            <span className="ml-[0.08em] text-[0.5em] font-bold tracking-normal">Mt</span>
          </p>
          <p className="mx-auto mt-4 max-w-sm text-xl leading-tight md:text-2xl">
            de nourriture perdue ou gaspillée chaque année, rien qu'en France.
          </p>
          <p className="mt-3 font-mono text-xs tracking-[0.15em] text-cream/55 uppercase">
            Source — ADEME, 2016
          </p>
        </div>
      </div>

      <p
        data-reveal
        className="mx-auto mt-[26vh] max-w-4xl text-center font-serif text-4xl leading-[1.02] md:text-7xl"
      >
        Pendant ce temps, à quelques rues de là, des associations cherchent de quoi{" "}
        <span className="text-lime">remplir leurs étagères.</span>
      </p>
    </section>
  );
}
