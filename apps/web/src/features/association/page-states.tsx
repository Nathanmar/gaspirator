import { type ErrorComponentProps, useRouter } from "@tanstack/react-router";
import { LoaderCircle } from "lucide-react";

import { FormAlert } from "@/components/form-controls";
import { ApiError, FALLBACK_MESSAGE, NetworkError } from "@/lib/api-client";

export function PagePending() {
	return (
		<p role="status" className="flex items-center gap-3 pt-10 text-cream/70">
			<LoaderCircle className="size-5 animate-spin" aria-hidden="true" />
			Chargement…
		</p>
	);
}

export function PageError({ error }: ErrorComponentProps) {
	const router = useRouter();
	const message =
		error instanceof ApiError || error instanceof NetworkError
			? error.message
			: FALLBACK_MESSAGE;

	return (
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
	);
}
