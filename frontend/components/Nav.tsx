import Link from "next/link";
import { Radar } from "lucide-react";

const LINKS = [
  { href: "/research/new", label: "New Investigation" },
  { href: "/history", label: "Research History" },
  { href: "/methodology", label: "Methodology" },
  { href: "/settings", label: "Settings" },
];

export default function Nav({ active = "" }: { active?: string }) {
  return (
    <header className="border-b border-line/70 sticky top-0 z-40 bg-ink/90 backdrop-blur">
      <div className="max-w-[1240px] mx-auto px-6 h-16 flex items-center gap-8">
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <span className="w-8 h-8 rounded-md bg-accent/15 border border-accent/40 flex items-center justify-center">
            <Radar size={17} className="text-accent" />
          </span>
          <span className="leading-none">
            <span className="block font-semibold tracking-tight text-[15px]">SIGNAL HUNTER X</span>
            <span className="block text-[10px] uppercase tracking-[0.18em] text-ter mt-1">AI Research Engine</span>
          </span>
        </Link>
        <nav className="hidden md:flex items-center gap-1 text-sm">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`px-3 py-2 rounded-md ${active === l.href ? "text-accent bg-accent/10" : "text-sec hover:text-pri hover:bg-surf2"}`}
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto">
          <Link href="/research/new" className="bg-accent text-ink text-sm font-semibold px-4 py-2 rounded-md hover:brightness-110">
            Launch Investigation
          </Link>
        </div>
      </div>
    </header>
  );
}
