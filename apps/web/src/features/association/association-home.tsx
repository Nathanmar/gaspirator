import type { AssociationHomeData } from "./association-loader";
import { CollectionsSection } from "./collections-section";
import { eyebrowClass, pageTitleClass } from "./space-ui";
import { RadiusPicker, SuppliersSection } from "./suppliers-section";

export function AssociationHome({
	data,
	radius,
}: {
	data: AssociationHomeData;
	radius: number;
}) {
	const { firstname, association, reservations, suppliers } = data;

	return (
		// data-fit-screen: SpaceLayout holds this page to the screen height and the left half on
		// large screens; the map takes the right half.
		<div data-fit-screen className="flex flex-col gap-10 lg:min-h-0 lg:flex-1">
			<div>
				<p className={eyebrowClass}>Espace association</p>
				<h1 className={pageTitleClass}>Bonjour {firstname}</h1>
				<p className="mt-3 text-base leading-snug text-cream/70 md:text-lg">
					{association.name} · {association.address.city}
				</p>
			</div>

			<RadiusPicker radius={radius} />

			<SuppliersSection
				suppliers={suppliers}
				radius={radius}
				center={association.location}
			/>

			{/* The only part that scrolls on large screens. */}
			<div className="lg:-mr-4 lg:min-h-0 lg:flex-1 lg:overflow-y-auto lg:pr-4">
				<CollectionsSection reservations={reservations} />
			</div>
		</div>
	);
}
