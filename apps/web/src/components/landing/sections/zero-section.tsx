import { JoinButtons } from "../join-buttons";
import { LogoMark } from "../logo-mark";

export function ZeroSection() {
	return (
		<section
			id="rejoindre"
			data-stage
			data-zero
			className="relative flex min-h-svh flex-col"
		>
			<div className="flex min-h-svh flex-col items-center justify-center px-5 py-28 text-center">
				<h2 className="relative">
					<span
						data-zero-top
						className="block font-display text-[16vw] leading-[0.9] font-extrabold tracking-[-0.04em] md:text-[9vw]"
					>
						Objectif
					</span>
					<span
						data-zero-word
						className="block font-display text-[16vw] leading-[0.9] font-extrabold tracking-[-0.04em] text-lime md:text-[9vw]"
					>
						zéro
					</span>
					<span className="sr-only">gaspillage</span>
				</h2>
				<p
					data-reveal
					className="mt-8 max-w-md text-lg leading-snug text-cream/70"
				>
					Chaque don publié, c'est un repas de plus servi, et un déchet de
					moins.
				</p>
				<JoinButtons data-reveal className="mt-10" />
			</div>

			<footer className="relative border-t border-cream/10 bg-ink/40 backdrop-blur-sm">
				<div className="flex flex-col gap-4 px-5 py-6 font-mono text-[11px] tracking-[0.18em] text-cream/70 uppercase md:flex-row md:items-center md:justify-between md:px-10">
					<span className="flex items-center gap-2 text-cream">
						<LogoMark className="h-6 w-auto" />
						Gaspirator © {new Date().getFullYear()}
					</span>
					<a href="#top" className="transition-colors hover:text-lime">
						Retour en haut ↑
					</a>
				</div>
			</footer>
		</section>
	);
}
