import { createFileRoute } from "@tanstack/react-router";

import { Skeleton } from "@/components/ui/skeleton";

export const Route = createFileRoute("/")({
  component: HomeComponent,
});

const card = "rounded-box border border-base-300 p-4 md:p-6";
// Horizontal page padding, shared with the header and the reviews bleed below
const gutter = "px-4 sm:px-6 lg:px-12 xl:px-20";

function SectionTitle() {
  return (
    <div className="flex flex-col items-center gap-2">
      <Skeleton className="h-7 w-48 md:h-9 md:w-64" />
      <Skeleton className="h-3 w-32 md:w-48" />
    </div>
  );
}

// Layout placeholder for the home page; content spec lives in docs/home-page.md
function HomeComponent() {
  return (
    <main aria-busy="true" className="flex w-full flex-col gap-12 py-8 md:gap-20 md:py-12 lg:gap-24">
      {/* Hero: stacked on mobile, text + illustration side by side from md */}
      <section aria-label="Hero" className={`grid gap-8 md:grid-cols-2 md:items-center lg:gap-16 ${gutter}`}>
        <div className="flex flex-col gap-4">
          <Skeleton className="h-6 w-40 rounded-full" />
          <Skeleton className="h-10 w-4/5 md:h-12 lg:h-14" />
          <Skeleton className="h-10 w-3/5 md:h-12 lg:h-14" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
          <div className="mt-2 flex flex-col gap-3 sm:flex-row">
            <Skeleton className="h-12 w-full rounded-full sm:w-48" />
            <Skeleton className="h-12 w-full rounded-full sm:w-36" />
          </div>
        </div>
        <Skeleton className="aspect-[4/3] w-full rounded-box md:aspect-square lg:aspect-[4/3]" />
      </section>

      {/* Partners */}
      <section aria-label="Partenaires" className={`flex flex-col items-center gap-4 ${gutter}`}>
        <Skeleton className="h-3 w-48" />
        <div className="flex w-full flex-wrap justify-center gap-6 md:justify-between lg:justify-evenly">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-6 w-16 md:h-8 md:w-24" />
          ))}
        </div>
      </section>

      {/* Features: 1 col, 2 cols from sm, wide/narrow bento from md */}
      <section aria-label="Fonctionnalités" className={`flex flex-col gap-6 md:gap-10 ${gutter}`}>
        <SectionTitle />
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-5 lg:gap-6">
          {["md:col-span-3", "md:col-span-2", "md:col-span-2", "md:col-span-3"].map((span, i) => (
            <div key={i} className={`${card} flex min-h-40 flex-col justify-end gap-2 md:min-h-56 ${span}`}>
              <Skeleton className="h-5 w-1/2" />
              <Skeleton className="h-3 w-3/4" />
              <Skeleton className="h-3 w-1/3" />
            </div>
          ))}
        </div>
      </section>

      {/* Why us: 1 → 2 → 4 columns */}
      <section aria-label="Pourquoi Gaspirator" className={`flex flex-col gap-6 md:gap-10 ${gutter}`}>
        <SectionTitle />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className={`${card} flex flex-col gap-3`}>
              <Skeleton className="size-8" />
              <Skeleton className="mt-4 h-4 w-1/2" />
              <Skeleton className="h-3 w-full" />
            </div>
          ))}
        </div>
      </section>

      {/* Reviews: 1 → 2 → 3 columns, no horizontal scroll */}
      <section aria-label="Avis" className={`flex flex-col gap-6 md:gap-10 ${gutter}`}>
        <SectionTitle />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 lg:gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className={`${card} flex flex-col gap-3 ${i === 3 ? "sm:hidden lg:flex" : ""}`}>
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-5/6" />
              <div className="mt-2 flex items-center gap-3">
                <Skeleton className="size-10 rounded-full" />
                <div className="flex flex-col gap-1">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="h-3 w-14" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ: stacked, title left / questions right from md */}
      <section aria-label="FAQ" className={`grid gap-6 md:grid-cols-[1fr_2fr] lg:gap-16 ${gutter}`}>
        <div className="flex flex-col gap-2">
          <Skeleton className="h-7 w-40 md:h-9" />
          <Skeleton className="h-3 w-56" />
        </div>
        <div className="flex flex-col gap-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <div className={gutter}>
        <section aria-label="Appel à l'action" className={`${card} grid gap-6 md:grid-cols-2 md:items-center md:p-10`}>
          <div className="flex flex-col gap-3">
            <Skeleton className="h-7 w-3/4 md:h-9" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="mt-2 h-12 w-full rounded-full sm:w-44" />
          </div>
          <Skeleton className="aspect-video w-full rounded-box" />
        </section>
      </div>

      {/* Footer: stacked on mobile, brand + link columns side by side from md */}
      <footer className={`grid gap-8 border-t border-base-300 pt-8 md:grid-cols-2 md:pt-12 ${gutter}`}>
        <div className="flex flex-col gap-3">
          <Skeleton className="h-7 w-28" />
          <Skeleton className="h-3 w-48" />
          <div className="flex max-w-sm gap-2">
            <Skeleton className="h-11 flex-1" />
            <Skeleton className="h-11 w-24" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-3">
          {[1, 2, 3].map((col) => (
            <div key={col} className="flex flex-col gap-2">
              <Skeleton className="h-4 w-20" />
              {[1, 2, 3].map((link) => (
                <Skeleton key={link} className="h-3 w-16" />
              ))}
            </div>
          ))}
        </div>
      </footer>
    </main>
  );
}
