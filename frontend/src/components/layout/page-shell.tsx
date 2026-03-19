import { type ReactNode } from "react";

interface PageShellProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function PageShell({
  title,
  subtitle,
  actions,
  children,
}: PageShellProps) {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
          {subtitle && (
            <p className="mt-1 text-gray-400">{subtitle}</p>
          )}
        </div>
        {actions && <div className="flex gap-3">{actions}</div>}
      </div>
      {children}
    </div>
  );
}
