import { MANIFESTO } from "../content";
import { SplitWords } from "../split-text";

export function VortexSection() {
  return (
    <section id="aspiration" data-stage data-vortex className="relative h-[300svh]">
      <div className="sticky top-0 flex h-svh flex-col justify-center px-5 md:px-10">
        <p className="max-w-[18ch] font-display text-[11vw] leading-[0.95] font-semibold tracking-[-0.035em] md:max-w-[22ch] md:text-[5.6vw]">
          <SplitWords
            text={MANIFESTO}
            accentClassName="font-serif font-normal text-lime tracking-normal"
          />
        </p>
      </div>
    </section>
  );
}
