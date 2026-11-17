import type { AssociationHomeData } from "./association-loader";
import { CollectionsSection } from "./collections-section";
import { eyebrowClass, pageTitleClass } from "./space-ui";
import { SuppliersSection } from "./suppliers-section";

export function AssociationHome({
	data,
	radius,
}: {
	data: AssociationHomeData;
	radius: number;
}) {
	const { firstname, association, reservations, suppliers } = data;

	return (
		<>
			<p className={eyebrowClass}>Espace association</p>
			<h1 className={pageTitleClass}>Bonjour {firstname}</h1>
			<p className="mt-4 text-base leading-snug text-cream/70 md:text-lg">
				{association.name} · {association.address.city}
			</p>

			<div className="mt-10 grid gap-12 lg:grid-cols-[minmax(0,24rem)_minmax(0,1fr)] lg:items-start lg:gap-10">
				<CollectionsSection reservations={reservations} />
				<SuppliersSection
					suppliers={suppliers}
					radius={radius}
					center={association.location}
				/>
			</div>
		</>
	);
}
