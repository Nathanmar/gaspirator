import { LogoMark } from "./logo-mark";

export function Preloader() {
  return (
    <div
      data-preloader
      className="fixed inset-0 z-[70] flex flex-col justify-between bg-ink px-5 py-5 [clip-path:inset(0_0_0_0)] md:px-10 md:py-8"
    >
      <div className="flex items-start justify-between font-mono text-[11px] tracking-[0.2em] text-cream/60 uppercase">
        <span className="flex items-center gap-3">
          <LogoMark className="h-8 w-auto" />
          Gaspirator®
        </span>
        <span className="text-right">
          Récupération
          <br />
          du surplus
        </span>
      </div>
      <div className="flex items-end justify-between gap-6">
        <div className="mb-[2vw] h-px flex-1 bg-cream/15">
          <div data-preloader-bar className="h-full origin-left scale-x-0 bg-lime" />
        </div>
        <div className="overflow-hidden">
          <span
            data-preloader-count
            className="block font-display text-[26vw] leading-[0.8] font-bold tracking-[-0.05em] tabular-nums [font-stretch:75%] md:text-[19vw]"
          >
            000
          </span>
        </div>
      </div>
    </div>
  );
}
