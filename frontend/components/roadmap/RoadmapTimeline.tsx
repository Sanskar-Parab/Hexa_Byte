"use client";

import { Check, Clock, Circle, SkipForward, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { PhaseCard } from "./PhaseCard";
import { RoadmapPhase } from "@/types";

interface RoadmapTimelineProps {
  phases: RoadmapPhase[];
  onUpdateStatus: (phaseId: string, status: string) => void;
}

const statusConfig = {
  not_started: { icon: Circle, color: "text-slate-400", bg: "bg-slate-100", border: "border-slate-300" },
  in_progress: { icon: Clock, color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-300" },
  completed: { icon: Check, color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-300" },
};

const adaptationConfig = {
  full: { label: null, color: "", bg: "" },
  adapted: { label: "Accelerated", color: "text-blue-600", bg: "bg-blue-50" },
  skipped: { label: "Skipped", color: "text-slate-500", bg: "bg-slate-50" },
};

export function RoadmapTimeline({ phases, onUpdateStatus }: RoadmapTimelineProps) {
  return (
    <div className="relative">
      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-200" />

      <div className="space-y-8">
        {phases.map((phase) => {
          const config = statusConfig[phase.status];
          const adaptation = adaptationConfig[phase.adaptation_mode];
          const Icon = phase.adaptation_mode === "skipped" ? SkipForward : config.icon;
          const isSkipped = phase.adaptation_mode === "skipped";
          const isAdapted = phase.adaptation_mode === "adapted";

          return (
            <div key={phase.id} className={cn("relative flex gap-6", isSkipped && "opacity-60")}>
              <div className="relative z-10">
                <div className={cn(
                  "flex h-12 w-12 items-center justify-center rounded-full border-2 bg-white shadow-sm",
                  isSkipped ? "border-slate-300 border-dashed" : config.border
                )}>
                  <Icon className={cn("h-5 w-5", isSkipped ? "text-slate-400" : config.color)} />
                </div>
              </div>

              <div className="flex-1 pb-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-slate-500">Phase {phase.phase_number}</span>
                  <span className={cn(
                    "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                    isSkipped ? "bg-slate-100 text-slate-500" : isAdapted ? "bg-blue-50 text-blue-600" : config.bg + " " + config.color
                  )}>
                    {isSkipped && <SkipForward className="h-3 w-3" />}
                    {isAdapted && <Zap className="h-3 w-3" />}
                    {isSkipped ? "Skipped" : isAdapted ? "Accelerated" : phase.status.replace("_", " ")}
                  </span>
                </div>
                <PhaseCard phase={phase} onUpdateStatus={onUpdateStatus} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
