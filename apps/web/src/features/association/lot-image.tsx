import { type LucideIcon, Package, ShoppingBasket, Soup } from "lucide-react";

import { cn } from "@/lib/utils";

import type { LotSummary, QuantityUnit } from "./association-api";

const UNIT_ICONS: Record<QuantityUnit, LucideIcon> = {
	portions: Soup,
	kg: ShoppingBasket,
	pieces: Package,
};

const BACKGROUNDS = [
	"from-lime/25 via-cream/5 to-tomato/10",
	"from-tomato/20 via-cream/5 to-lime/15",
	"from-cream/15 via-lime/10 to-lime/25",
];

/**
 * Picture of a lot. The contract has no photo yet (requested change): an illustration of the kind
 * of food (meal, weighed goods, items) holds its place, its colour varying from one lot to another.
 */
export function LotImage({
	lot,
	className,
	iconClassName = "size-10",
}: {
	lot: Pick<LotSummary, "id" | "unit">;
	className?: string;
	iconClassName?: string;
}) {
	const Icon = UNIT_ICONS[lot.unit];

	return (
		<div
			aria-hidden="true"
			className={cn(
				"flex items-center justify-center bg-linear-to-br",
				BACKGROUNDS[lot.id % BACKGROUNDS.length],
				className,
			)}
		>
			<Icon className={cn("text-cream/35", iconClassName)} strokeWidth={1.5} />
		</div>
	);
}
