"use client";

import { type ReactNode, useEffect, useState } from "react";

interface ResponsiveGridProps {
  children: ReactNode;
  className?: string;
  /** Columns at mobile (default: 1) */
  cols?: number;
  /** Columns at sm (640px+) */
  sm?: number;
  /** Columns at lg (1024px+) */
  lg?: number;
  /** Custom template for lg breakpoint, e.g. "340px 1fr" */
  lgTemplate?: string;
  /** Gap in rem (default: 1.5) */
  gap?: number;
}

export function ResponsiveGrid({
  children,
  className = "",
  cols = 1,
  sm,
  lg,
  lgTemplate,
  gap = 1.5,
}: ResponsiveGridProps) {
  const [width, setWidth] = useState(1200); // SSR default above lg

  useEffect(() => {
    const update = () => setWidth(window.innerWidth);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  let template: string;
  if (lgTemplate && width >= 1024) {
    template = lgTemplate;
  } else if (lg && width >= 1024) {
    template = `repeat(${lg}, 1fr)`;
  } else if (sm && width >= 640) {
    template = `repeat(${sm}, 1fr)`;
  } else {
    template = `repeat(${cols}, 1fr)`;
  }

  return (
    <div
      className={className}
      style={{
        display: "grid",
        gridTemplateColumns: template,
        gap: `${gap}rem`,
      }}
    >
      {children}
    </div>
  );
}
