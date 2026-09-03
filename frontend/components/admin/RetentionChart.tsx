"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { TrendingUp } from "lucide-react";
import type { CohortMetrics } from "@/types";

export function RetentionChart({ metrics }: { metrics: CohortMetrics }) {
  const data = [
    { label: "3 Months", rate: metrics.retention_3_month_rate },
    { label: "6 Months", rate: metrics.retention_6_month_rate },
    { label: "12 Months", rate: metrics.retention_12_month_rate },
  ];
  const hasData = data.some((d) => d.rate !== null);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold text-ink">Retention Over Time</CardTitle>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <EmptyState
            icon={TrendingUp}
            title="No retention data yet"
            description="Retention rates appear once employed trainees reach a check-in milestone with a confirmed status."
          />
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ebebeb" />
                <XAxis dataKey="label" tick={{ fontSize: 12, fill: "#888888" }} />
                <YAxis tick={{ fontSize: 12, fill: "#888888" }} domain={[0, 100]} unit="%" />
                <Tooltip
                  formatter={(v: number | string) => (v === null || v === undefined ? "No data" : `${v}%`)}
                  contentStyle={{ borderRadius: "8px", border: "1px solid #ebebeb", fontSize: "13px" }}
                />
                <Bar dataKey="rate" radius={[6, 6, 0, 0]}>
                  {data.map((d, i) => (
                    <Cell key={i} fill={d.rate === null ? "#ebebeb" : "#171717"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
