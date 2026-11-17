import { cn } from "@/lib/utils";

import { AUDIENCES } from "../content";

// Compact supplier / charity cards, stacked next to the manifesto in the vortex section.
export function ActorCards() {
  return (
    <div id="acteurs" className="flex flex-col gap-5">
      {AUDIENCES.map((audience) => {
        const lime = audience.tone === "lime";
        return (
          <article
            key={audience.id}
            id={audience.id}
            data-actor
            className="glass grid gap-4 rounded-2xl p-5 md:grid-cols-[1fr_1.3fr] md:gap-8 md:p-7"
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
              <h2 className="mt-3 font-display text-2xl leading-tight font-bold tracking-[-0.02em] md:text-4xl">
                {audience.title}
              </h2>
            </div>
            <ul className="divide-y divide-cream/10 self-center border-y border-cream/10">
              {audience.features.map((feature, i) => (
                <li key={feature} className="flex items-center justify-between gap-3 py-2.5">
                  <span className="text-sm md:text-base">{feature}</span>
                  <span className="font-mono text-[10px] text-cream/40">0{i + 1}</span>
                </li>
              ))}
            </ul>
          </article>
        );
      })}
    </div>
  );
}
