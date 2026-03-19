import { type ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string;
  icon?: ReactNode;
  sub?: string;
  subColor?: string;
}

export function StatCard({ label, value, icon, sub, subColor }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-surface-border bg-surface p-5 shadow-lg shadow-black/20 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-black/30">
      <div className="flex items-start justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          {label}
        </span>
        {icon && (
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface-light text-brand">
            {icon}
          </span>
        )}
      </div>
      <p className="mt-2 text-2xl font-bold">{value}</p>
      {sub && (
        <span
          className={`mt-1 inline-block rounded-md px-2 py-0.5 text-xs font-semibold ${
            subColor ?? "text-gray-500"
          }`}
        >
          {sub}
        </span>
      )}
    </div>
  );
}
