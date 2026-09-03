import { cn } from "@/lib/utils";
import type { TrainingRelevanceLevel } from "@/types";

const CONFIG: Record<TrainingRelevanceLevel, { label: string; className: string }> = {
  high: { label: "HIGH RELEVANCE", className: "bg-link-soft text-link-deep" },
  medium: { label: "MEDIUM RELEVANCE", className: "bg-warn-soft text-warn-deep" },
  low: { label: "LOW RELEVANCE", className: "bg-err-soft text-err-deep" },
  unknown: { label: "UNKNOWN", className: "bg-canvas-soft2 text-mute" },
};

export function RelevanceBadge({ level, className }: { level: TrainingRelevanceLevel; className?: string }) {
  const config = CONFIG[level] ?? CONFIG.unknown;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[10px] font-medium tracking-wide",
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  );
}
