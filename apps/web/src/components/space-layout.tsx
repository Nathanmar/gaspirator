import { Link, useNavigate } from "@tanstack/react-router";
import { LogOut } from "lucide-react";
import type { ReactNode } from "react";

import { LogoMark } from "@/components/landing/logo-mark";
import { useLogout } from "@/features/auth/use-logout";

export function SpaceLayout({ children }: { children: ReactNode }) {
	const logOut = useLogout();
	const navigate = useNavigate();

	async function handleLogout() {
		await logOut();
		await navigate({ to: "/" });
	}

	return (
		<div className="landing relative isolate flex min-h-svh flex-col bg-ink font-display text-cream">
			<div
				aria-hidden="true"
				className="landing-glow pointer-events-none fixed inset-0 -z-10"
			/>

			<header className="flex items-center justify-between gap-4 px-5 py-4 md:px-10 md:py-6">
				<Link
					to="/"
					className="inline-flex items-center gap-2.5"
					aria-label="Gaspirator, retour à l'accueil"
				>
					<LogoMark className="h-9 w-auto" />
					<span className="text-xl font-bold tracking-[-0.03em]">
						gaspirator
					</span>
				</Link>

				<button
					type="button"
					onClick={() => void handleLogout()}
					className="inline-flex size-11 shrink-0 items-center justify-center gap-2 rounded-full border border-cream/15 text-[11px] font-semibold tracking-[0.18em] whitespace-nowrap uppercase transition-colors hover:bg-cream/10 focus-visible:bg-cream/10 min-[380px]:w-auto min-[380px]:px-4"
				>
					<LogOut className="size-4" aria-hidden="true" />
					{/* Icon only on the narrowest phones, where the label does not fit next to the logo. */}
					<span className="sr-only min-[380px]:not-sr-only">
						Se déconnecter
					</span>
				</button>
			</header>

			<main className="mx-auto w-full max-w-6xl flex-1 px-5 pt-4 pb-16 md:px-10 md:pt-8">
				{children}
			</main>

			<div aria-hidden="true" className="grain" />
		</div>
	);
}
