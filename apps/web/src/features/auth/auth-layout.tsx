import { Link } from "@tanstack/react-router";
import type { CSSProperties, ReactNode, Ref } from "react";

import { LogoMark } from "@/components/landing/logo-mark";
import { cn } from "@/lib/utils";

type AuthLayoutProps = {
	// Small lime line above the title, as on the landing page.
	eyebrow: string;
	title: string;
	// Lets a page move the focus to the title, e.g. when a confirmation replaces a long form.
	titleRef?: Ref<HTMLHeadingElement>;
	description?: ReactNode;
	// Under the card: link to the other auth page, styled here.
	footer?: ReactNode;
	// The registration form needs more room than the login form.
	wide?: boolean;
	// Short message screens (e.g. "Demande envoyée"): centred on every screen, each line rising in turn.
	centered?: boolean;
	// Shown above the eyebrow, e.g. the success badge.
	mark?: ReactNode;
	children: ReactNode;
};

/**
 * Shell of the login and registration pages, in the landing page's visual identity: the `landing`
 * class brings its colour tokens (paper background, lime and tomato accents), plus its glow,
 * glass card and grain. One column on mobile; the content is centred on larger screens.
 */
export function AuthLayout({
	eyebrow,
	title,
	titleRef,
	description,
	footer,
	wide,
	centered,
	mark,
	children,
}: AuthLayoutProps) {
	// Staggered entrance of the centred screens; `--d` is the rank of the line.
	const reveal = (rank: number) =>
		centered ? ({ "--d": rank } as CSSProperties) : undefined;
	const revealClass = centered && "reveal-up";

	return (
		<div className="landing relative isolate flex min-h-svh flex-col bg-ink font-display text-cream">
			<div
				aria-hidden="true"
				className="landing-glow pointer-events-none fixed inset-0 -z-10"
			/>

			<header className="px-5 py-4 md:px-10 md:py-6">
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
			</header>

			<main
				className={cn(
					"flex flex-1 justify-center px-5 pt-6 pb-16 md:items-center md:px-10 lg:pt-0 lg:pb-6",
					// Bottom padding matches the header height, so the block sits at the screen's centre.
					centered && "items-center pb-24 lg:pb-20",
				)}
			>
				{/* Wide: intro beside the card on large screens, so the long form fits without scrolling. */}
				<div
					className={cn(
						"w-full",
						wide
							? "max-w-2xl lg:grid lg:max-w-6xl lg:grid-cols-[1fr_minmax(0,40rem)] lg:items-center lg:gap-16"
							: "max-w-md",
						centered && "text-center",
					)}
				>
					<div>
						{mark}
						<p
							className={cn(
								"text-sm font-semibold tracking-[0.12em] text-lime uppercase",
								revealClass,
							)}
							style={reveal(0)}
						>
							{eyebrow}
						</p>
						<h1
							ref={titleRef}
							tabIndex={-1}
							className={cn(
								"mt-3 text-5xl leading-[0.95] font-extrabold tracking-[-0.04em] outline-none md:text-6xl",
								revealClass,
							)}
							style={reveal(1)}
						>
							{title}
						</h1>
						{description && (
							<p
								className={cn(
									"mt-4 text-base leading-snug text-cream/70 md:text-lg",
									revealClass,
								)}
								style={reveal(2)}
							>
								{description}
							</p>
						)}
					</div>

					<div className={cn(revealClass)} style={reveal(3)}>
						<div
							className={cn(
								"glass mt-8 rounded-[28px] p-5 sm:p-8",
								wide && "lg:mt-0 lg:p-6",
							)}
						>
							{children}
						</div>

						{footer && (
							<p className="mt-4 text-center text-sm text-cream/70 [&_a]:font-semibold [&_a]:text-cream [&_a]:underline [&_a]:underline-offset-4">
								{footer}
							</p>
						)}
					</div>
				</div>
			</main>

			<div aria-hidden="true" className="grain" />
		</div>
	);
}
