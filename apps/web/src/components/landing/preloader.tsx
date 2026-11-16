import { Skeleton } from "@/components/ui/skeleton";

// Skeleton of the hero layout, shown until the 3D scene and fonts are ready.
export function Preloader() {
  const block = "rounded-md bg-cream/10";
  return (
    <div
      data-preloader
      role="status"
      aria-label="Chargement"
      className="fixed inset-0 z-[70] flex flex-col bg-ink px-5 pt-4 md:px-10 md:pt-6"
    >
      <div className="flex items-center justify-between">
        <Skeleton className={`${block} h-8 w-36`} />
        <Skeleton className={`${block} hidden h-9 w-64 rounded-full md:block`} />
        <Skeleton className={`${block} h-9 w-28 rounded-full`} />
      </div>
      <div className="flex flex-1 flex-col items-center justify-center gap-4 pb-16">
        <Skeleton className={`${block} h-4 w-64 md:h-5 md:w-80`} />
        <Skeleton className={`${block} h-[min(15vw,19svh)] w-[min(80vw,62svh*1.4)]`} />
        <Skeleton className={`${block} mt-2 h-8 w-[min(90vw,36rem)] md:h-12`} />
        <Skeleton className={`${block} h-4 w-[min(85vw,30rem)]`} />
        <Skeleton className={`${block} h-4 w-[min(70vw,22rem)]`} />
      </div>
    </div>
  );
}
