import Link from "next/link";

const PLATFORM_LINKS = [
  { label: "Borrower Portal", href: "#" },
  { label: "Risk Assessment", href: "#" },
  { label: "Security Audit", href: "#" },
];

const LEGAL_LINKS = [
  { label: "Terms of Service", href: "#" },
  { label: "Privacy Policy", href: "#" },
  { label: "Risk Disclosure", href: "#" },
];

export function Footer() {
  return (
    <footer className="border-t border-white/[0.06] bg-[#0B0F1A]">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div style={{ display: "grid", gap: "2rem", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-xs font-bold text-gray-950">
                C
              </span>
              <span className="text-sm font-bold">
                Cre<span className="text-brand">DeFi</span>
              </span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-gray-500">
              Bridging the gap between DeFi liquidity and real-world credit
              opportunities. Secure, transparent, and high-yield lending.
            </p>
          </div>

          {/* Platform */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Platform</h4>
            <ul className="mt-3 space-y-2.5">
              {PLATFORM_LINKS.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-gray-500 transition-colors duration-200 hover:text-gray-300"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Legal</h4>
            <ul className="mt-3 space-y-2.5">
              {LEGAL_LINKS.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-gray-500 transition-colors duration-200 hover:text-gray-300"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-white/[0.06] pt-6 sm:flex-row">
          <p className="text-xs text-gray-600">
            &copy; {new Date().getFullYear()} CreDeFi Protocol. All rights
            reserved.
          </p>
          <div className="flex items-center gap-2 rounded-full border border-surface-border px-3 py-1 text-xs text-gray-500">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Mainnet v1.0.4
          </div>
        </div>
      </div>
    </footer>
  );
}
