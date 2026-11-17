import { useRef } from "react";

import { Cursor } from "./cursor";
import { Hud } from "./hud";
import { Preloader } from "./preloader";
import { CircuitSection } from "./sections/circuit-section";
import { HeroSection } from "./sections/hero-section";
import { ProblemSection } from "./sections/problem-section";
import { VortexSection } from "./sections/vortex-section";
import { ZeroSection } from "./sections/zero-section";
import { useLandingMotion } from "./use-landing-motion";

export function Landing() {
	const rootRef = useRef<HTMLDivElement>(null);
	const canvasRef = useRef<HTMLCanvasElement>(null);
	useLandingMotion(rootRef, canvasRef);

	return (
		// `overflow-x-clip`: some sections start their animations off to the right (actor cards, the
		// horizontal circuit track); without it the page is wider than a phone screen and the header
		// button ends up off-screen. `clip` rather than `hidden` keeps sticky and pinned sections working.
		<div
			ref={rootRef}
			className="landing relative isolate overflow-x-clip bg-ink font-display text-cream"
		>
			<div
				aria-hidden="true"
				className="landing-glow pointer-events-none fixed inset-0 opacity-50"
			/>
			<canvas
				ref={canvasRef}
				className="pointer-events-none fixed inset-0 h-full w-full opacity-40"
			/>

			<Preloader />
			<Hud />

			<main className="relative">
				<HeroSection />
				<ProblemSection />
				<VortexSection />
				<CircuitSection />
				<ZeroSection />
			</main>

			<div aria-hidden="true" className="grain" />
			<Cursor />
		</div>
	);
}
