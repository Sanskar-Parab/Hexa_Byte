"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Check, RotateCcw, Play, SkipForward, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";
import { RoadmapPhase } from "@/types";

interface PhaseCardProps {
  phase: RoadmapPhase;
  onUpdateStatus: (phaseId: string, status: string) => void;
  defaultExpanded?: boolean;
}

export function PhaseCard({ phase, onUpdateStatus, defaultExpanded }: PhaseCardProps) {
  const [expanded, setExpanded] = useState(!!defaultExpanded);

  const isSkipped = phase.adaptation_mode === "skipped";
  const isAdapted = phase.adaptation_mode === "adapted";

  const getStatusAction = () => {
    if (isSkipped) {
      return { label: "Include Phase", nextStatus: "not_started", icon: SkipForward, variant: "secondary" as const };
    }
    switch (phase.status) {
      case "not_started":
        return { label: "Start Phase", nextStatus: "in_progress", icon: Play, variant: "default" as const };
      case "in_progress":
        return { label: "Complete Phase", nextStatus: "completed", icon: Check, variant: "default" as const };
      case "completed":
        return { label: "Reopen Phase", nextStatus: "in_progress", icon: RotateCcw, variant: "secondary" as const };
      default:
        return { label: "Start Phase", nextStatus: "in_progress", icon: Play, variant: "default" as const };
    }
  };

  const action = getStatusAction();
  const ActionIcon = action.icon;

  return (
    <Card
      className={cn(
        "overflow-hidden transition-shadow",
        isSkipped && "border-dashed bg-canvas-soft"
      )}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className={cn("text-base font-semibold sm:text-lg", isSkipped ? "text-mute" : "text-ink")}>
                {phase.title}
              </h3>
              {!isSkipped && phase.status !== "completed" && (
                <StatusBadge status={phase.status} />
              )}
              {phase.status === "completed" && !isSkipped && <StatusBadge status="completed" />}
            </div>
            <p className={cn("mt-1 text-sm leading-relaxed", isSkipped ? "text-mute" : "text-body")}>
              {phase.objective}
            </p>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="shrink-0 rounded-lg p-1.5 hover:bg-canvas-soft transition-colors"
            aria-label={expanded ? "Collapse phase" : "Expand phase"}
          >
            {expanded ? <ChevronUp className="h-5 w-5 text-mute" /> : <ChevronDown className="h-5 w-5 text-mute" />}
          </button>
        </div>

        {(isAdapted || isSkipped) && (
          <div
            className={cn(
              "mt-3 flex items-start gap-2 rounded-lg px-3 py-2 text-xs font-medium",
              isSkipped ? "bg-canvas-soft2 text-mute" : "bg-link-soft text-link-deep"
            )}
          >
            <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            {isSkipped
              ? "Skipped — you already demonstrate this skill level."
              : "This phase was adapted to your current skill level."}
          </div>
        )}

        <div className="mt-3 flex flex-wrap gap-1.5">
          <Badge variant="outline" className="text-xs">{phase.duration_weeks} weeks</Badge>
          {phase.skills.slice(0, 3).map((skill) => (
            <Badge key={skill} variant="secondary" className="text-xs">{skill}</Badge>
          ))}
          {phase.skills.length > 3 && (
            <Badge variant="secondary" className="text-xs">+{phase.skills.length - 3}</Badge>
          )}
        </div>

        {expanded && (
          <div className="mt-4 space-y-4 border-t border-hairline pt-4">
            {phase.skills.length > 0 && (
              <div>
                <p className="mb-2 text-sm font-medium text-ink">
                  {isAdapted ? "Quick Review Skills" : "Skills"}
                </p>
                <div className="flex flex-wrap gap-2">
                  {phase.skills.map((skill) => (
                    <Badge key={skill} variant="outline" className="text-xs">{skill}</Badge>
                  ))}
                </div>
              </div>
            )}

            {phase.activities.length > 0 && (
              <div>
                <p className="mb-2 text-sm font-medium text-ink">
                  {isAdapted ? "Accelerated Activities" : "Activities"}
                </p>
                <ul className="space-y-1.5">
                  {phase.activities.map((activity, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-body">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-hairline-strong" />
                      {activity}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {phase.project && (
              <div>
                <p className="mb-2 text-sm font-medium text-ink">Project</p>
                <p className="text-sm text-body">{phase.project}</p>
              </div>
            )}

            {phase.completion_criteria.length > 0 && (
              <div>
                <p className="mb-2 text-sm font-medium text-ink">Completion Criteria</p>
                <ul className="space-y-1.5">
                  {phase.completion_criteria.map((criteria, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-body">
                      <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-link" />
                      {criteria}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <Button
              onClick={() => onUpdateStatus(phase.id, action.nextStatus)}
              variant={action.variant}
              size="sm"
            >
              <ActionIcon className="mr-2 h-4 w-4" />
              {action.label}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
