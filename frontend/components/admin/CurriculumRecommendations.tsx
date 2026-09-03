"use client";

import { Lightbulb } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Badge } from "@/components/ui/badge";
import type { CurriculumRecommendationRow } from "@/types";

export function CurriculumRecommendations({ recommendations }: { recommendations: CurriculumRecommendationRow[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
          <Lightbulb className="h-4 w-4 text-mute" />
          Curriculum Recommendations
        </CardTitle>
      </CardHeader>
      <CardContent>
        {recommendations.length === 0 ? (
          <EmptyState
            icon={Lightbulb}
            title="No curriculum flags right now"
            description="This flags a skill only when it's a recurring gap (30%+ of a program's trainees) alongside that program's placement rate falling below the cross-program average — both computed from real, aggregated outcome data."
          />
        ) : (
          <div className="space-y-3">
            {recommendations.map((rec, i) => (
              <div key={`${rec.training_program_id}-${rec.skill}-${i}`} className="rounded-lg border border-hairline p-4">
                <div className="mb-1.5 flex flex-wrap items-center gap-2">
                  <Badge variant="warning">{rec.skill}</Badge>
                  <span className="text-sm font-medium text-ink">{rec.training_program_name}</span>
                  <span className="text-xs text-mute">· {rec.provider_name}</span>
                </div>
                <p className="text-sm text-body">{rec.recommendation}</p>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-mute">
                  <span>{rec.affected_trainee_percentage}% of trainees affected</span>
                  <span>Program placement: {rec.program_placement_rate}%</span>
                  <span>Cross-program average: {rec.overall_placement_rate}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
