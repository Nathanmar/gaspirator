import { cn } from "@/lib/utils";

import { AUDIENCES } from "../content";
import { SectionLabel } from "../section-label";

export function ActorsSection() {
  return (
    <section
      id="acteurs"
      data-stage
      className="relative px-5 pt-[20vh] pb-[16vh] md:px-10 lg:pr-32 xl:pr-36"
    >
      <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <SectionLabel index="04" title="Les acteurs" />
        <p data-reveal className="max-w-md text-cream/60 md:text-right">
          Un seul circuit, pour ceux qui donnent comme pour ceux qui récupèrent.
        </p>
      </div>

      <div className="mt-[46svh] grid gap-5 md:mt-[52svh] md:grid-cols-2 md:gap-6">
        {AUDIENCES.map((audience) => {
          const lime = audience.tone === "lime";
          return (
            <article
              key={audience.id}
              id={audience.id}
              data-actor
              className="glass flex scroll-mt-24 flex-col justify-between gap-12 rounded-[28px] p-6 md:min-h-[560px] md:p-10"
            >
              <div>
                <p
                  className={cn(
                    "font-mono text-[11px] tracking-[0.2em] uppercase",
                    lime ? "text-lime" : "text-tomato",
                  )}
                >
                  {audience.eyebrow}
                </p>
                <h3 className="mt-6 font-display text-5xl leading-[0.9] font-bold tracking-[-0.04em] [font-stretch:80%] md:text-[4.6vw]">
                  {audience.title}
                </h3>
                <p className="mt-4 font-serif text-2xl text-cream/70 italic">{audience.who}</p>
              </div>
              <ul className="divide-y divide-cream/10 border-y border-cream/10">
                {audience.features.map((feature, i) => (
                  <li key={feature} className="flex items-center justify-between gap-4 py-3.5">
                    <span className="text-lg">{feature}</span>
                    <span className="font-mono text-[10px] text-cream/40">0{i + 1}</span>
                  </li>
                ))}
              </ul>
            </article>
          );
        })}
      </div>
    </section>
  );
}
