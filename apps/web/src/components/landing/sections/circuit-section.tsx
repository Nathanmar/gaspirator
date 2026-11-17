import { Check } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { STEPS, SUPPLIERS, type Supplier } from "../content";

function PublishVisual() {
  return (
    <div className="rounded-2xl border border-cream/10 bg-ink/60 p-4 text-sm">
      <p className="font-mono text-[10px] tracking-[0.2em] text-cream/45 uppercase">Nouveau don</p>
      <dl className="mt-3 divide-y divide-cream/10">
        {[
          ["Produit", "Lasagnes végétariennes"],
          ["Quantité", "42 portions"],
          ["À consommer avant", "Ce soir"],
          ["Retrait", "18:00 – 19:30"],
        ].map(([label, value]) => (
          // Short screens drop the third row so the card still fits.
          <div
            key={label}
            className="flex justify-between gap-4 py-2 [@media(max-height:760px)]:nth-3:hidden"
          >
            <dt className="text-cream/70">{label}</dt>
            <dd className="text-right">{value}</dd>
          </div>
        ))}
      </dl>
      <div className="mt-3 rounded-full bg-lime py-2 text-center font-mono text-[11px] font-semibold tracking-[0.18em] text-ink uppercase">
        Publier
      </div>
    </div>
  );
}

function ReserveVisual() {
  const mapRef = useRef<HTMLDivElement>(null);
  const [selectedId, setSelectedId] = useState<Supplier["id"]>(SUPPLIERS[0].id);
  const selected = SUPPLIERS.find((supplier) => supplier.id === selectedId) ?? SUPPLIERS[0];
  // The map owns the pins; it only needs the starting selection.
  const initialId = useRef(selectedId).current;

  // The map (a second WebGL context plus tiles) is only created once the card gets close.
  useEffect(() => {
    const container = mapRef.current;
    if (!container) return;
    let cleanup: (() => void) | undefined;
    let cancelled = false;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        import("../map/create-reserve-map")
          .then(({ createReserveMap }) => {
            if (!cancelled) {
              cleanup = createReserveMap(container, {
                selectedId: initialId,
                onSelect: setSelectedId,
              });
            }
          })
          .catch((error: unknown) => console.warn("Reserve map unavailable", error));
      },
      { rootMargin: "100%" },
    );
    observer.observe(container);
    return () => {
      cancelled = true;
      observer.disconnect();
      cleanup?.();
    };
  }, [initialId]);

  return (
    <div className="relative h-full min-h-48 overflow-hidden rounded-2xl border border-cream/10 bg-[#e9e4d8] text-sm">
      {/* MapLibre forces `position: relative` on its container, so size it explicitly. `isolate`
          keeps the raised (selected) pin under the donation row. */}
      <div ref={mapRef} className="isolate h-full w-full" />
      {/* Map data credit, required by the OpenStreetMap and CARTO licences. */}
      <p className="pointer-events-none absolute top-1.5 right-2 font-mono text-[8px] tracking-wide text-cream/70">
        © OpenStreetMap · CARTO
      </p>
      <div className="absolute inset-x-2 bottom-2 flex items-center justify-between gap-3 rounded-xl border border-cream/10 bg-ink/85 py-2 pr-2 pl-3 backdrop-blur-md">
        <div
          key={selected.id}
          aria-live="polite"
          className="min-w-0 animate-in duration-300 fade-in slide-in-from-bottom-1"
        >
          <p className="truncate">{selected.name}</p>
          <p className="truncate font-mono text-[10px] tracking-[0.12em] text-cream/70 uppercase">
            {selected.distance} · {selected.portions} portions
          </p>
        </div>
        <span className="shrink-0 rounded-full bg-lime px-3 py-1.5 font-mono text-[10px] font-semibold tracking-[0.15em] text-ink uppercase">
          Réserver
        </span>
      </div>
    </div>
  );
}

function PickupVisual() {
  return (
    <div className="rounded-2xl border border-cream/10 bg-ink/60 p-4 text-center">
      <p className="font-mono text-[10px] tracking-[0.2em] text-cream/45 uppercase">
        Code de retrait
      </p>
      <div className="mt-4 flex justify-center gap-2">
        {["4", "8", "2", "9"].map((digit, i) => (
          <span
            key={i}
            className="grid h-16 w-12 place-items-center rounded-xl border border-lime/40 bg-lime/10 font-mono text-3xl text-lime"
          >
            {digit}
          </span>
        ))}
      </div>
      <p className="mt-4 text-sm text-cream/70">À présenter au fournisseur</p>
    </div>
  );
}

function ConfirmVisual() {
  return (
    <div className="rounded-2xl border border-cream/10 bg-ink/60 p-4 text-center">
      <div className="mx-auto grid size-16 place-items-center rounded-full bg-lime text-ink">
        <Check className="size-8" strokeWidth={2.5} />
      </div>
      <p className="mt-4 text-lg">Remise confirmée</p>
      <p className="font-mono text-[10px] tracking-[0.15em] text-cream/70 uppercase">
        42 portions · 18:47
      </p>
    </div>
  );
}

const VISUALS = [PublishVisual, ReserveVisual, PickupVisual, ConfirmVisual];

export function CircuitSection() {
  return (
    <section
      id="circuit"
      data-stage
      data-circuit
      className="relative h-svh overflow-hidden"
    >
      <div
        data-circuit-track
        className="grid h-full w-max grid-flow-col content-center gap-5 px-5 will-change-transform md:gap-8 md:px-10"
      >
        <div className="flex w-[84vw] shrink-0 flex-col justify-center md:w-[40vw]">
          <h2 className="font-display text-[13vw] leading-[0.86] font-bold tracking-[-0.045em] [font-stretch:80%] md:text-[6.4vw]">
            Du frigo
            <br />
            au{" "}
            <span className="font-serif font-normal tracking-normal text-lime">repas</span>,
            <br />
            en quatre étapes.
          </h2>
        </div>

        {STEPS.map((step, i) => {
          const Visual = VISUALS[i];
          return (
            <article
              key={step.index}
              data-step
              className="glass glass-solid flex h-[min(38rem,calc(100svh-12rem))] min-h-[26rem] w-[80vw] shrink-0 flex-col gap-5 rounded-[28px] p-6 md:w-[27vw] md:min-w-[340px] md:p-7"
            >
              <div className="flex items-start justify-between">
                <span className="font-display text-6xl leading-none font-bold tracking-[-0.05em] text-cream/15 [font-stretch:75%]">
                  {step.index}
                </span>
                <span className="font-mono text-[10px] tracking-[0.18em] text-cream/70 uppercase">
                  {step.actor}
                </span>
              </div>
              {/* The visual takes whatever height is left so the card never grows past the
                  space between the header and the progress bar. */}
              <div className="flex min-h-0 flex-1 flex-col justify-center">
                <Visual />
              </div>
              <div>
                <h3 className="font-display text-4xl font-bold tracking-[-0.03em]">{step.title}</h3>
                <p className="mt-2 leading-snug text-cream/65">{step.text}</p>
              </div>
            </article>
          );
        })}
        <div className="w-[8vw] shrink-0 lg:w-36 xl:w-40" />
      </div>

      <div className="absolute inset-x-5 bottom-16 h-px bg-cream/15 md:inset-x-10 md:bottom-20">
        <div data-circuit-progress className="h-full origin-left scale-x-0 bg-lime" />
      </div>
    </section>
  );
}
