"use client";

import { Briefcase, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";

interface CareerOverviewProps {
  targetCareer: string | null;
  matchScore: number;
  readiness: number;
}

export function CareerOverview({ targetCareer, matchScore, readiness }: CareerOverviewProps) {
  if (!targetCareer) {
    return (
      <EmptyState
        icon={Briefcase}
        title="No target career yet"
        description="Choose a career to start tracking your readiness."
        actionLabel="Browse Careers"
        actionHref="/careers"
      />
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
          <Briefcase className="h-4 w-4 text-mute" />
          Career Readiness
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h3 className="text-xl font-semibold tracking-tight text-ink">{targetCareer}</h3>
          <Badge variant="success" className="mt-2">
            <TrendingUp className="mr-1 h-3 w-3" />
            {matchScore}% Match
          </Badge>
        </div>

        <div>
          <div className="mb-1.5 flex items-center justify-between text-sm">
            <span className="text-body">Readiness</span>
            <span className="font-semibold text-ink">{readiness}%</span>
          </div>
          <Progress value={readiness} className="h-2 bg-hairline" indicatorClassName="bg-ink" />
        </div>

        <div className="rounded-lg bg-canvas-soft p-3">
          <p className="text-xs text-body">
            Keep working through your roadmap to raise your readiness score.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
