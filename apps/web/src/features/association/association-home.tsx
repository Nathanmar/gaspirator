import { type ErrorComponentProps, useRouter } from "@tanstack/react-router";
import { LoaderCircle } from "lucide-react";

import { FormAlert } from "@/components/form-controls";
import { SpaceLayout } from "@/components/space-layout";
import { ApiError, NetworkError } from "@/lib/api-client";

import type { AssociationHomeData } from "./association-loader";
import { CollectionsSection } from "./collections-section";
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
		<SpaceLayout>
			<p className="text-sm font-semibold tracking-[0.12em] text-lime uppercase">
				Espace association
			</p>
			<h1 className="mt-3 text-5xl leading-[0.95] font-extrabold tracking-[-0.04em] wrap-anywhere md:text-6xl">
				Bonjour {firstname}
			</h1>
			<p className="mt-4 text-base leading-snug text-cream/70 md:text-lg">
				{association.name} · {association.address.city}
			</p>

			<div className="mt-10 grid gap-12 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)] lg:items-start lg:gap-10">
				<CollectionsSection reservations={reservations} />
				<SuppliersSection suppliers={suppliers} radius={radius} />
			</div>
		</SpaceLayout>
	);
}

export function AssociationHomePending() {
	return (
		<SpaceLayout>
			<p role="status" className="flex items-center gap-3 pt-10 text-cream/70">
				<LoaderCircle className="size-5 animate-spin" aria-hidden="true" />
				Chargement de votre espace…
			</p>
		</SpaceLayout>
	);
}

export function AssociationHomeError({ error }: ErrorComponentProps) {
	const router = useRouter();
	const message =
		error instanceof ApiError || error instanceof NetworkError
			? error.message
			: "Une erreur inattendue est survenue. Réessayez plus tard.";

	return (
		<SpaceLayout>
			<div className="flex max-w-md flex-col items-start gap-4 pt-10">
				<FormAlert>{message}</FormAlert>
				<button
					type="button"
					onClick={() => void router.invalidate()}
					className="inline-flex h-11 items-center rounded-full bg-lime px-5 text-xs font-semibold tracking-[0.18em] text-ink uppercase"
				>
					Réessayer
				</button>
			</div>
		</SpaceLayout>
	);
}
