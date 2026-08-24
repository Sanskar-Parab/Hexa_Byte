"use client";

import { Check, Clock, Circle } from "lucide-react";
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

export function RoadmapTimeline({ phases, onUpdateStatus }: RoadmapTimelineProps) {
  return (
    <div className="relative">
      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-200" />

      <div className="space-y-8">
        {phases.map((phase) => {
          const config = statusConfig[phase.status];
          const Icon = config.icon;

          return (
            <div key={phase.id} className="relative flex gap-6">
              <div className="relative z-10">
                <div className={cn("flex h-12 w-12 items-center justify-center rounded-full border-2 bg-white shadow-sm", config.border)}>
                  <Icon className={cn("h-5 w-5", config.color)} />
                </div>
              </div>

              <div className="flex-1 pb-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-slate-500">Phase {phase.phase_number}</span>
                  <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium", config.bg, config.color)}>
                    {phase.status.replace("_", " ")}
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
