import { Link, useNavigate } from "@tanstack/react-router";
import { Bell, LogOut, Settings, User } from "lucide-react";
import type { ReactNode } from "react";

import { LogoMark } from "@/components/landing/logo-mark";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useLogout } from "@/features/auth/use-logout";

const iconButtonClass =
	"grid size-9 place-items-center rounded-lg text-cream/70 transition-colors hover:bg-cream/10 hover:text-cream focus-visible:bg-cream/10 focus-visible:text-cream focus-visible:outline-none";

export function SpaceLayout({ children }: { children: ReactNode }) {
	const logOut = useLogout();
	const navigate = useNavigate();

	async function handleLogout() {
		await logOut();
		await navigate({ to: "/" });
	}

	return (
		// A page marked `data-fit-screen` gets exactly the screen height and, with the header, the
		// left half of it on large screens: the page fills the right half itself.
		<div className="group/space landing relative isolate flex min-h-svh flex-col bg-ink font-display text-cream lg:has-[[data-fit-screen]]:h-svh">
			<div
				aria-hidden="true"
				className="landing-glow pointer-events-none fixed inset-0 -z-10"
			/>

			<header className="flex items-center justify-between gap-4 px-5 py-4 md:px-10 md:py-6 lg:group-has-[[data-fit-screen]]/space:w-1/2 xl:group-has-[[data-fit-screen]]/space:px-16">
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

				{/* Over the top right corner of the map when the page fills the right half. */}
				<nav
					aria-label="Compte"
					className="z-20 flex shrink-0 gap-1 rounded-xl border border-cream/10 bg-ink/85 p-1 backdrop-blur-md lg:group-has-[[data-fit-screen]]/space:fixed lg:group-has-[[data-fit-screen]]/space:top-8 lg:group-has-[[data-fit-screen]]/space:right-8"
				>
					{/* shortcut: settings and notifications have no page yet, link them once they do. */}
					<button
						type="button"
						aria-disabled="true"
						title="Bientôt disponible"
						className={`${iconButtonClass} cursor-not-allowed opacity-50`}
					>
						<Settings className="size-4" aria-hidden="true" />
						<span className="sr-only">Paramètres (bientôt disponible)</span>
					</button>
					<button
						type="button"
						aria-disabled="true"
						title="Bientôt disponible"
						className={`${iconButtonClass} cursor-not-allowed opacity-50`}
					>
						<Bell className="size-4" aria-hidden="true" />
						<span className="sr-only">Notifications (bientôt disponible)</span>
					</button>
					<DropdownMenu>
						<DropdownMenuTrigger
							aria-label="Mon compte"
							className={`${iconButtonClass} data-popup-open:bg-cream/10 data-popup-open:text-cream`}
						>
							<User className="size-4" aria-hidden="true" />
						</DropdownMenuTrigger>
						<DropdownMenuContent
							align="end"
							sideOffset={8}
							className="w-auto min-w-44 rounded-xl border border-cream/10 bg-ink p-1 font-display text-cream ring-0"
						>
							<DropdownMenuItem
								onClick={() => void handleLogout()}
								className="gap-2.5 rounded-lg px-3 py-2.5 text-sm text-cream focus:bg-cream/10 focus:text-cream"
							>
								<LogOut className="size-4" aria-hidden="true" />
								Se déconnecter
							</DropdownMenuItem>
						</DropdownMenuContent>
					</DropdownMenu>
				</nav>
			</header>

			<main className="flex w-full flex-1 flex-col px-5 pt-4 pb-16 md:px-10 md:pt-8 lg:has-[[data-fit-screen]]:min-h-0 lg:has-[[data-fit-screen]]:w-1/2 lg:has-[[data-fit-screen]]:pb-8 xl:has-[[data-fit-screen]]:px-16">
				{children}
			</main>

			<div aria-hidden="true" className="grain" />
		</div>
	);
}
