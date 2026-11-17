import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import type { ReactNode } from "react";

import { useAuthStore } from "@/features/auth/auth-store";
import { cn } from "@/lib/utils";

import { JOIN_LINKS } from "./content";

const buttonClass =
	"group inline-flex items-center justify-between gap-4 rounded-full py-2 pr-2 pl-6 font-mono text-[11px] font-semibold tracking-[0.18em] text-ink uppercase";

function Arrow() {
	return (
		<span className="grid size-9 place-items-center rounded-full bg-ink text-cream transition-transform duration-300 group-hover:rotate-45">
			<ArrowUpRight className="size-4" />
		</span>
	);
}

// "Je suis fournisseur" / "Je suis une association", shown in the hero and the final section;
// once logged in, a single way into one's space.
export function JoinButtons({
	className,
	...props
}: React.HTMLAttributes<HTMLDivElement>) {
	const isLoggedIn = useAuthStore((state) => state.tokens !== null);

	let buttons: ReactNode;
	if (isLoggedIn) {
		buttons = (
			// shortcut: only the association space exists, use homePath(getMe()) once suppliers have one.
			<Link
				to="/association"
				data-magnetic
				className={cn(buttonClass, "bg-lime")}
			>
				Accéder à mon espace
				<Arrow />
			</Link>
		);
	} else {
		buttons = JOIN_LINKS.map((link) => (
			<a
				key={link.href}
				href={link.href}
				data-magnetic
				className={cn(
					buttonClass,
					link.tone === "lime" ? "bg-lime" : "bg-tomato",
				)}
			>
				{link.label}
				<Arrow />
			</a>
		));
	}

	return (
		<div
			className={cn("flex flex-col gap-3 sm:flex-row", className)}
			{...props}
		>
			{buttons}
		</div>
	);
}
