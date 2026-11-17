import { SplitWords } from "../split-text";

// Animated in use-landing-motion ([data-problem]): stats line by line, slash spin, quote word by word.
export function ProblemSection() {
	return (
		<section
			id="constat"
			data-stage
			data-problem
			className="relative px-5 md:px-10"
		>
			{/* The two figures stacked on the left, the consequence on the right, on one screen. */}
			<div className="mx-auto grid min-h-svh max-w-6xl content-center items-center gap-12 py-24 md:grid-cols-2 md:gap-16">
				<div className="flex flex-col gap-10">
					<div data-stat>
						<p className="font-display text-[24vw] leading-[0.85] font-extrabold tracking-[-0.05em] md:text-[min(9vw,17svh)]">
							1
							<span
								data-slash
								className="mx-[0.04em] inline-block align-[0.12em] text-[0.7em] font-bold text-tomato"
							>
								/
							</span>
							3
						</p>
						<p className="mt-3 max-w-sm text-xl leading-tight md:text-2xl">
							de la nourriture produite dans le monde est perdue ou gaspillée.
						</p>
						<p className="mt-2 font-mono text-xs tracking-[0.15em] text-cream/55 uppercase">
							Source — FAO, 2011
						</p>
					</div>

					<div data-stat>
						<p className="font-display text-[24vw] leading-[0.85] font-extrabold tracking-[-0.05em] md:text-[min(9vw,17svh)]">
							<span data-count-to="10">10</span>
							<span className="ml-[0.08em] text-[0.5em] font-bold tracking-normal">
								Mt
							</span>
						</p>
						<p className="mt-3 max-w-sm text-xl leading-tight md:text-2xl">
							de nourriture perdue ou gaspillée chaque année, rien qu'en France.
						</p>
						<p className="mt-2 font-mono text-xs tracking-[0.15em] text-cream/55 uppercase">
							Source — ADEME, 2016
						</p>
					</div>
				</div>

				<p
					data-quote
					className="font-serif text-3xl leading-[1.1] font-semibold md:text-5xl"
				>
					<SplitWords
						text="Pendant ce temps, à quelques rues de là, des associations cherchent de quoi *remplir* *leurs* *étagères.*"
						accentClassName="text-lime"
					/>
				</p>
			</div>
		</section>
	);
}
