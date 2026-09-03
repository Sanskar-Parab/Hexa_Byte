"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { UserX } from "lucide-react";
import type { NonPlacementCategoryRow } from "@/types";

const CATEGORY_LABELS: Record<string, string> = {
  skill_gap: "Skill Gap",
  profile_incomplete: "Incomplete Profile",
  unknown: "Unknown",
};

export function NonPlacementChart({ categories }: { categories: NonPlacementCategoryRow[] }) {
  if (categories.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-ink">Why Trainees Aren&apos;t Placed</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={UserX}
            title="No non-placement data"
            description="This breaks down deterministically, from stored evidence only — it appears once there are unplaced trainees to analyze."
          />
        </CardContent>
      </Card>
    );
  }

  const data = categories.map((c) => ({
    ...c,
    label: CATEGORY_LABELS[c.category] || c.category,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold text-ink">Why Trainees Aren&apos;t Placed</CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{ height: Math.max(data.length * 48, 140) }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ top: 5, right: 24, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ebebeb" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 12, fill: "#888888" }} />
              <YAxis type="category" dataKey="label" width={130} tick={{ fontSize: 12, fill: "#171717" }} />
              <Tooltip
                formatter={(v: number, _n, item: any) => [`${v}% (${item.payload.trainee_count} trainees)`, "Share"]}
                contentStyle={{ borderRadius: "8px", border: "1px solid #ebebeb", fontSize: "13px" }}
              />
              <Bar dataKey="percentage" fill="#ee0000" radius={[0, 6, 6, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-3 text-xs text-mute">
          Categories are derived only from stored evidence (skill proficiency, project completion, resume status). No category is shown without supporting data.
        </p>
      </CardContent>
    </Card>
  );
}
