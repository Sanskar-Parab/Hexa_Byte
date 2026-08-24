"use client";

import { AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkillGapInfo } from "@/types";

interface SkillGapOverviewProps {
  gaps: SkillGapInfo[];
}

export function SkillGapOverview({ gaps }: SkillGapOverviewProps) {
  if (gaps.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <AlertTriangle className="h-12 w-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-900 mb-1">No Skill Gaps</h3>
          <p className="text-sm text-slate-500">Complete your profile to see skill gap analysis.</p>
        </CardContent>
      </Card>
    );
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "High": return <Badge className="bg-rose-100 text-rose-700">High</Badge>;
      case "Medium": return <Badge className="bg-amber-100 text-amber-700">Medium</Badge>;
      default: return <Badge className="bg-slate-100 text-slate-600">Low</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          Top Skill Gaps
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {gaps.slice(0, 5).map((gap) => (
            <div key={gap.skill} className="flex items-center gap-3">
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-slate-700">{gap.skill}</span>
                  {getSeverityBadge(gap.gap_severity)}
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-slate-100 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full"
                      style={{ width: `${gap.target_level > 0 ? (gap.current_level / gap.target_level) * 100 : 0}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-500 w-12 text-right">
                    {gap.current_level}/{gap.target_level}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
