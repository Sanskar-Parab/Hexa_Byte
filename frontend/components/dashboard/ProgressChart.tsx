"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressData } from "@/types";

interface ProgressChartProps {
  data: ProgressData[];
}

export function ProgressChart({ data }: ProgressChartProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-sm text-body">No progress data available yet. Start your journey to see trends.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold text-ink">Progress Over Time</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ebebeb" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12, fill: "#888888" }}
                tickFormatter={(v) => {
                  const d = new Date(v);
                  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
                }}
              />
              <YAxis tick={{ fontSize: 12, fill: "#888888" }} />
              <Tooltip
                contentStyle={{
                  borderRadius: "8px",
                  border: "1px solid #ebebeb",
                  boxShadow: "0 4px 6px -1px rgba(0,0,0,0.06)",
                  fontSize: "13px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px" }} />
              <Line
                type="monotone"
                dataKey="skills_mastered"
                name="Skills Mastered"
                stroke="#171717"
                strokeWidth={2}
                dot={{ fill: "#171717", r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="projects_completed"
                name="Projects"
                stroke="#0070f3"
                strokeWidth={2}
                dot={{ fill: "#0070f3", r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="assessment_score"
                name="Assessment Score"
                stroke="#f5a623"
                strokeWidth={2}
                dot={{ fill: "#f5a623", r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
