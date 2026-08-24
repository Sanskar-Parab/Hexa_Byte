"use client";

import { TrendingUp } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface DashboardHeaderProps {
  name: string;
  overallProgress: number;
  careerReadiness: number;
}

export function DashboardHeader({ name, overallProgress, careerReadiness }: DashboardHeaderProps) {
  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="rounded-2xl bg-gradient-to-br from-blue-600 to-blue-700 p-6 sm:p-8 text-white shadow-xl shadow-blue-500/20">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">
            {greeting()}, {name?.split(" ")[0] || "there"}
          </h1>
          <p className="mt-1 text-blue-100">
            Here&apos;s your career development progress
          </p>
        </div>
        <div className="flex items-center gap-2 bg-white/10 rounded-lg px-4 py-2">
          <TrendingUp className="h-5 w-5 text-emerald-300" />
          <span className="text-sm font-medium">{careerReadiness}% Career Ready</span>
        </div>
      </div>

      <div className="mt-6 grid sm:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-blue-100">Overall Progress</span>
            <span className="font-semibold">{overallProgress}%</span>
          </div>
          <Progress value={overallProgress} className="h-2.5 bg-white/20" indicatorClassName="bg-emerald-400" />
        </div>
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-blue-100">Career Readiness</span>
            <span className="font-semibold">{careerReadiness}%</span>
          </div>
          <Progress value={careerReadiness} className="h-2.5 bg-white/20" indicatorClassName="bg-amber-400" />
        </div>
      </div>
    </div>
  );
}
