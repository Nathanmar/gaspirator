import { Link, type LinkProps } from "@tanstack/react-router";
import { ArrowLeft, Phone } from "lucide-react";
import type { ReactNode } from "react";

export const sectionTitleClass =
	"text-2xl font-extrabold tracking-[-0.03em] md:text-3xl";

export const eyebrowClass =
	"text-sm font-semibold tracking-[0.12em] text-lime uppercase";

export const pageTitleClass =
	"mt-3 text-5xl leading-[0.95] font-extrabold tracking-[-0.04em] wrap-anywhere md:text-6xl";

export const labelClass =
	"text-xs font-semibold tracking-[0.14em] text-cream/70 uppercase";

export const pillLinkClass =
	"inline-flex h-11 items-center gap-2 rounded-full border border-cream/15 px-4 text-sm font-semibold transition-colors hover:bg-cream/10";

export function EmptyState({
	title,
	children,
}: {
	title: string;
	children?: ReactNode;
}) {
	return (
		<div className="mt-4 rounded-[28px] border border-dashed border-cream/20 p-6 text-center">
			<p className="font-semibold">{title}</p>
			{children && (
				<div className="mt-2 text-sm text-cream/70 [&_a]:font-semibold [&_a]:text-cream [&_a]:underline [&_a]:underline-offset-4">
					{children}
				</div>
			)}
		</div>
	);
}

export function BackLink({
	to,
	children,
}: {
	to: LinkProps["to"];
	children: ReactNode;
}) {
	return (
		<Link
			to={to}
			className="-ml-1 inline-flex h-11 items-center gap-2 px-1 text-sm font-semibold text-cream/70 transition-colors hover:text-cream"
		>
			<ArrowLeft className="size-4" aria-hidden="true" />
			{children}
		</Link>
	);
}

export function PhoneLink({ phone }: { phone: string }) {
	return (
		<a href={`tel:${phone.replace(/[^\d+]/g, "")}`} className={pillLinkClass}>
			<Phone className="size-4" aria-hidden="true" />
			{phone}
		</a>
	);
}
