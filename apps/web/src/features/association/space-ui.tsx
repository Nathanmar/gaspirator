import type { ReactNode } from "react";

export const sectionTitleClass =
	"text-2xl font-extrabold tracking-[-0.03em] md:text-3xl";

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
