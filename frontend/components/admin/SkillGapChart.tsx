"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Compass } from "lucide-react";
import type { SkillGapRow } from "@/types";

export function SkillGapChart({ gaps, title = "Most Common Skill Gaps" }: { gaps: SkillGapRow[]; title?: string }) {
  if (gaps.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-ink">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Compass}
            title="No skill gap data yet"
            description="Skill gaps are computed by comparing each trainee's demonstrated skills against what their training program teaches."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold text-ink">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{ height: Math.max(gaps.length * 44, 120) }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={gaps} layout="vertical" margin={{ top: 5, right: 24, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ebebeb" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 12, fill: "#888888" }} />
              <YAxis type="category" dataKey="skill" width={110} tick={{ fontSize: 12, fill: "#171717" }} />
              <Tooltip
                formatter={(v: number, _n, item: any) => [`${v}% (${item.payload.trainee_count} trainees)`, "Gap prevalence"]}
                contentStyle={{ borderRadius: "8px", border: "1px solid #ebebeb", fontSize: "13px" }}
              />
              <Bar dataKey="percentage" fill="#f5a623" radius={[0, 6, 6, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
