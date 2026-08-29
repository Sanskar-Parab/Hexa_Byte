"use client";

import { Compass } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { SkillBar } from "@/components/ui/skill-bar";
import { SkillGapInfo } from "@/types";

interface SkillGapOverviewProps {
  gaps: SkillGapInfo[];
}

export function SkillGapOverview({ gaps }: SkillGapOverviewProps) {
  const normalizedGaps = (gaps || []).map((gap: any) => {
    if (typeof gap === "string") {
      return { skill: gap, current_level: 0, target_level: 5, gap_severity: "Medium" };
    }
    const skillName = gap?.skill || gap?.skill_name || gap?.name || "Skill Gap";
    const current = gap?.current_level ?? gap?.user_proficiency ?? 0;
    const target = gap?.target_level ?? 5;
    const gapSize = gap?.gap_size ?? (target - current);
    const severity = gap?.gap_severity || (gapSize >= 4 ? "High" : gapSize >= 2 ? "Medium" : "Low");
    return { skill: skillName, current_level: current, target_level: target, gap_severity: severity };
  });

  if (normalizedGaps.length === 0) {
    return (
      <EmptyState
        icon={Compass}
        title="No skill gaps yet"
        description="Complete your profile and pick a career to see your skill gap analysis."
      />
    );
  }

  const severityVariant = (severity: string) =>
    severity === "High" ? "destructive" : severity === "Medium" ? "warning" : "secondary";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
          <Compass className="h-4 w-4 text-mute" />
          Your Skill Profile
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {normalizedGaps.slice(0, 5).map((gap, idx) => (
            <div key={gap.skill || idx}>
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-sm font-medium text-ink">{gap.skill}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-mute">
                    {gap.current_level}/{gap.target_level}
                  </span>
                  <Badge variant={severityVariant(gap.gap_severity) as any} className="text-[10px]">
                    {gap.gap_severity}
                  </Badge>
                </div>
              </div>
              <SkillBar proficiency={gap.current_level} targetLevel={gap.target_level} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
