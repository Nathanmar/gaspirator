import { MANIFESTO } from "../content";
import { SplitWords } from "../split-text";
import { ActorCards } from "./actors-section";

// Manifesto on the left (revealed word by word while pinned), who it's for on the right.
export function VortexSection() {
	return (
		<section
			id="aspiration"
			data-stage
			data-vortex
			className="relative md:h-[200svh]"
		>
			<div className="grid min-h-svh items-center gap-10 px-5 py-20 md:sticky md:top-0 md:h-svh md:grid-cols-[1fr_1.5fr] md:gap-12 md:px-10">
				<p className="font-display text-[8vw] leading-[1.05] font-semibold tracking-[-0.03em] md:text-[min(3.8vw,7svh)]">
					<SplitWords text={MANIFESTO} accentClassName="text-lime" />
				</p>
				<ActorCards />
			</div>
		</section>
	);
}
