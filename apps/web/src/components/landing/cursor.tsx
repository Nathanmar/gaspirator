export function Cursor() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-[80] hidden" data-cursor>
      <div
        data-cursor-ring
        className="absolute top-0 left-0 -mt-5 -ml-5 size-10 rounded-full border border-cream/50 transition-[scale,background-color,border-color] duration-300 ease-out"
      />
      <div
        data-cursor-dot
        className="absolute top-0 left-0 -mt-[3px] -ml-[3px] size-1.5 rounded-full bg-lime"
      />
    </div>
  );
}
