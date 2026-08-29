"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { PhaseCard } from "./PhaseCard";
import { RoadmapPhase } from "@/types";

interface RoadmapTimelineProps {
  phases: RoadmapPhase[];
  onUpdateStatus: (phaseId: string, status: string) => void;
}

function TimelineDot({ phase }: { phase: RoadmapPhase }) {
  const isSkipped = phase.adaptation_mode === "skipped";

  if (isSkipped) {
    return (
      <div className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-dashed border-hairline-strong bg-canvas" />
    );
  }

  if (phase.status === "completed") {
    return (
      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-ink text-white shadow-card">
        <Check className="h-4 w-4" />
      </div>
    );
  }

  if (phase.status === "in_progress") {
    return (
      <div className="relative flex h-9 w-9 items-center justify-center">
        <span className="absolute inline-flex h-full w-full animate-pulse rounded-full bg-warn/30" />
        <div className="relative flex h-7 w-7 items-center justify-center rounded-full border-2 border-warn bg-warn-soft" />
      </div>
    );
  }

  return (
    <div className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-hairline bg-canvas" />
  );
}

export function RoadmapTimeline({ phases, onUpdateStatus }: RoadmapTimelineProps) {
  return (
    <div className="relative">
      <div className="absolute left-[18px] top-2 bottom-2 w-px bg-hairline" />

      <div className="space-y-6">
        {phases.map((phase) => {
          const isCurrent = phase.status === "in_progress" && phase.adaptation_mode !== "skipped";

          return (
            <div key={phase.id} className={cn("relative flex gap-5", phase.adaptation_mode === "skipped" && "opacity-70")}>
              <div className="relative z-10 shrink-0 pt-0.5">
                <TimelineDot phase={phase} />
              </div>

              <div className="min-w-0 flex-1 pb-1">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs uppercase tracking-wide text-mute">
                    Phase {phase.phase_number}
                  </span>
                  {isCurrent && (
                    <span className="inline-flex items-center rounded-full bg-ink px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-wide text-white">
                      Current
                    </span>
                  )}
                </div>
                <PhaseCard phase={phase} onUpdateStatus={onUpdateStatus} defaultExpanded={isCurrent} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
