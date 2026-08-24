"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Check, Clock, Play } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RoadmapPhase } from "@/types";

interface PhaseCardProps {
  phase: RoadmapPhase;
  onUpdateStatus: (phaseId: string, status: string) => void;
}

export function PhaseCard({ phase, onUpdateStatus }: PhaseCardProps) {
  const [expanded, setExpanded] = useState(false);

  const statusActions = {
    not_started: { label: "Start Phase", nextStatus: "in_progress", icon: Play, color: "bg-blue-600 hover:bg-blue-700" },
    in_progress: { label: "Mark Complete", nextStatus: "completed", icon: Check, color: "bg-emerald-600 hover:bg-emerald-700" },
    completed: { label: "Reopen", nextStatus: "not_started", icon: Clock, color: "bg-slate-600 hover:bg-slate-700" },
  };

  const action = statusActions[phase.status];
  const ActionIcon = action.icon;

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-slate-900">{phase.title}</h3>
            <p className="mt-1 text-sm text-slate-600">{phase.objective}</p>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 rounded-lg hover:bg-slate-100 transition-colors"
          >
            {expanded ? <ChevronUp className="h-5 w-5 text-slate-400" /> : <ChevronDown className="h-5 w-5 text-slate-400" />}
          </button>
        </div>

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
          <div className="mt-4 pt-4 border-t space-y-4">
            {phase.skills.length > 0 && (
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">Skills to Develop</p>
                <div className="flex flex-wrap gap-2">
                  {phase.skills.map((skill) => (
                    <Badge key={skill} variant="outline" className="text-xs">{skill}</Badge>
                  ))}
                </div>
              </div>
            )}

            {phase.activities.length > 0 && (
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">Activities</p>
                <ul className="space-y-1.5">
                  {phase.activities.map((activity, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-slate-400 shrink-0" />
                      {activity}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {phase.project && (
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">Project</p>
                <p className="text-sm text-slate-600">{phase.project}</p>
              </div>
            )}

            {phase.completion_criteria.length > 0 && (
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">Completion Criteria</p>
                <ul className="space-y-1.5">
                  {phase.completion_criteria.map((criteria, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                      <Check className="mt-0.5 h-3.5 w-3.5 text-emerald-500 shrink-0" />
                      {criteria}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <Button
              onClick={() => onUpdateStatus(phase.id, action.nextStatus)}
              className={action.color}
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
