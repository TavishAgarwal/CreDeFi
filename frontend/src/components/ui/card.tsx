import { type ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: boolean;
  hover?: boolean;
}

export function Card({ children, className = "", padding = true, hover = true }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-surface-border bg-surface shadow-lg shadow-black/20 ${
        padding ? "p-6" : ""
      } ${
        hover ? "transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-black/30 hover:border-surface-light" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}
