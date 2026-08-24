"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface SkillGapChartProps {
  gaps: { skill: string; current_level: number; target_level: number }[];
}

export function SkillGapChart({ gaps }: SkillGapChartProps) {
  const data = gaps.map((gap) => ({
    skill: gap.skill.length > 15 ? gap.skill.slice(0, 15) + "…" : gap.skill,
    Current: gap.current_level,
    Required: gap.target_level,
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 10, top: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis type="number" domain={[0, 5]} tick={{ fontSize: 12 }} />
          <YAxis type="category" dataKey="skill" tick={{ fontSize: 12 }} width={100} />
          <Tooltip
            contentStyle={{
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)",
            }}
          />
          <Legend />
          <Bar dataKey="Current" fill="#3b82f6" radius={[0, 4, 4, 0]} />
          <Bar dataKey="Required" fill="#e2e8f0" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
