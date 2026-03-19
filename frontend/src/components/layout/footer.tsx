import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-surface-border bg-gray-950">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-brand text-xs font-bold text-gray-950">
            C
          </span>
          <span className="text-sm text-gray-400">
            &copy; {new Date().getFullYear()} CreDeFi Protocol. All rights
            reserved.
          </span>
        </div>
        <div className="flex gap-6 text-sm text-gray-500">
          <Link href="#" className="transition-colors hover:text-gray-300">
            Terms of Service
          </Link>
          <Link href="#" className="transition-colors hover:text-gray-300">
            Privacy Policy
          </Link>
          <Link href="#" className="transition-colors hover:text-gray-300">
            Documentation
          </Link>
        </div>
      </div>
    </footer>
  );
}
