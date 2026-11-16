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
    <div ref={rootRef} className="landing relative isolate bg-ink font-display text-cream">
      <div aria-hidden="true" className="landing-glow pointer-events-none fixed inset-0 opacity-50" />
      <canvas
        ref={canvasRef}
        aria-hidden="true"
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
