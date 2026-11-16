import { Link } from "@tanstack/react-router";

import { Skeleton } from "./ui/skeleton";

// Logo, section links (md+) and CTA; links are placeholders until sections exist
export default function Header() {
  return (
    <header className="border-b border-base-300">
      <div className="flex items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-12 xl:px-20">
        <Link to="/" className="text-lg font-semibold">
          Gaspirator
        </Link>
        <nav aria-label="Sections" className="hidden gap-6 md:flex">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-3 w-16" />
          ))}
        </nav>
        <Skeleton className="h-9 w-28 rounded-full" />
      </div>
    </header>
  );
}
