"use client";

import { Progress } from "@/components/ui/progress";

interface AssessmentProgressProps {
  current: number;
  total: number;
}

export function AssessmentProgress({ current, total }: AssessmentProgressProps) {
  const percentage = Math.round((current / total) * 100);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-600">Question {current} of {total}</span>
        <span className="font-medium text-slate-900">{percentage}%</span>
      </div>
      <Progress value={percentage} className="h-2" />
    </div>
  );
}
