"use client";

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
    <div>
      <p className="font-mono text-xs uppercase tracking-wider text-mute">
        {greeting()}, {name?.split(" ")[0] || "there"}
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
        Your Next Move
      </h1>
      <p className="mt-2 max-w-xl text-sm text-body">
        Know where you are, know where you&apos;re going, know what to do next.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 sm:max-w-md">
        <div className="rounded-xl border border-hairline bg-canvas p-4 shadow-card">
          <div className="flex items-center justify-between text-xs text-mute">
            <span>Overall Progress</span>
            <span className="font-semibold text-ink">{overallProgress}%</span>
          </div>
          <Progress value={overallProgress} className="mt-2 h-1.5 bg-hairline" indicatorClassName="bg-ink" />
        </div>
        <div className="rounded-xl border border-hairline bg-canvas p-4 shadow-card">
          <div className="flex items-center justify-between text-xs text-mute">
            <span>Career Readiness</span>
            <span className="font-semibold text-ink">{careerReadiness}%</span>
          </div>
          <Progress value={careerReadiness} className="mt-2 h-1.5 bg-hairline" indicatorClassName="bg-link" />
        </div>
      </div>
    </div>
  );
}
