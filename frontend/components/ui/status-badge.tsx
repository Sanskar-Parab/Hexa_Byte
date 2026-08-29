import { CheckCircle2, CircleDot, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

type Status = "completed" | "in_progress" | "not_started" | string;

const CONFIG: Record<string, { label: string; className: string; icon: typeof Circle }> = {
  completed: { label: "Completed", className: "bg-link-soft text-link-deep", icon: CheckCircle2 },
  in_progress: { label: "In Progress", className: "bg-warn-soft text-warn-deep", icon: CircleDot },
  not_started: { label: "Not Started", className: "bg-canvas-soft2 text-mute", icon: Circle },
};

export function StatusBadge({ status, className }: { status: Status; className?: string }) {
  const config = CONFIG[status] ?? CONFIG.not_started;
  const Icon = config.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        config.className,
        className
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {config.label}
    </span>
  );
}

const CONFIDENCE_CONFIG: Record<string, { label: string; className: string }> = {
  high: { label: "HIGH", className: "bg-link-soft text-link-deep" },
  medium: { label: "MEDIUM", className: "bg-warn-soft text-warn-deep" },
  low: { label: "LOW", className: "bg-canvas-soft2 text-mute" },
};

export function ConfidenceBadge({ confidence, className }: { confidence: string; className?: string }) {
  const config = CONFIDENCE_CONFIG[confidence?.toLowerCase()] ?? CONFIDENCE_CONFIG.low;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[10px] font-medium tracking-wide",
        config.className,
        className
      )}
    >
      {config.label} CONFIDENCE
    </span>
  );
}
