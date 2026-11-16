import { cn } from "@/lib/utils";

export function SectionLabel({
  index,
  title,
  className,
}: {
  index: string;
  title: string;
  className?: string;
}) {
  return (
    <p
      data-label
      className={cn(
        "flex items-center gap-3 font-mono text-[11px] tracking-[0.2em] text-cream/60 uppercase",
        className,
      )}
    >
      <span className="text-lime">{index}</span>
      <span data-label-line className="h-px w-10 origin-left bg-cream/40" />
      <span>{title}</span>
    </p>
  );
}
