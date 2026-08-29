"use client";

import { Progress } from "@/components/ui/progress";

interface AssessmentProgressProps {
  current: number;
  total: number;
}

export function AssessmentProgress({ current, total }: AssessmentProgressProps) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-body">Question {current} of {total}</span>
        <span className="font-medium text-ink">{percentage}%</span>
      </div>
      <Progress value={percentage} className="h-1.5 bg-hairline" indicatorClassName="bg-ink" />
    </div>
  );
}
