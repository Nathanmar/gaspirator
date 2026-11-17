import { ArrowUpRight } from "lucide-react";

import { cn } from "@/lib/utils";

import { JOIN_LINKS } from "./content";

// "Je suis fournisseur" / "Je suis une association", shown in the hero and the final section.
export function JoinButtons({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			className={cn("flex flex-col gap-3 sm:flex-row", className)}
			{...props}
		>
			{JOIN_LINKS.map((link) => (
				<a
					key={link.href}
					href={link.href}
					data-magnetic
					className={cn(
						"group inline-flex items-center justify-between gap-4 rounded-full py-2 pr-2 pl-6 font-mono text-[11px] font-semibold tracking-[0.18em] text-ink uppercase",
						link.tone === "lime" ? "bg-lime" : "bg-tomato",
					)}
				>
					{link.label}
					<span className="grid size-9 place-items-center rounded-full bg-ink text-cream transition-transform duration-300 group-hover:rotate-45">
						<ArrowUpRight className="size-4" />
					</span>
				</a>
			))}
		</div>
	);
}
