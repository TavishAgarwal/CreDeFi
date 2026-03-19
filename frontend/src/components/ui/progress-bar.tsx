interface ProgressBarProps {
  value: number;
  max?: number;
  color?: string;
  animated?: boolean;
}

export function ProgressBar({
  value,
  max = 100,
  color = "bg-brand",
  animated = true,
}: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-800/60">
      <div
        className={`relative h-full rounded-full transition-all duration-700 ease-out ${color}`}
        style={{ width: `${pct}%` }}
      >
        {animated && (
          <div className="absolute inset-0 shimmer-bar rounded-full" />
        )}
      </div>
    </div>
  );
}
