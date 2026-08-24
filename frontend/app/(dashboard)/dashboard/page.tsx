"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { CareerOverview } from "@/components/dashboard/CareerOverview";
import { SkillGapOverview } from "@/components/dashboard/SkillGapOverview";
import { WeeklyActions } from "@/components/dashboard/WeeklyActions";
import { ProgressChart } from "@/components/dashboard/ProgressChart";

export default function DashboardPage() {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [selectedCareer, setSelectedCareer] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedCareerId = localStorage.getItem("selectedCareerId");

    const loadData = async () => {
      try {
        const [dashData, recs] = await Promise.all([
          api.getDashboard().catch(() => null),
          api.getStoredRecommendations().catch(() => []),
        ]);
        setDashboardData(dashData);
        setRecommendations(recs);

        if (storedCareerId) {
          const matched = recs.find((r: any) => String(r.career_id) === String(storedCareerId));
          if (matched) {
            setSelectedCareer(matched);
          } else {
            api.getCareerDetail(storedCareerId).then(setSelectedCareer).catch(() => {});
          }
        } else if (recs.length > 0) {
          setSelectedCareer(recs[0]);
          localStorage.setItem("selectedCareerId", recs[0].career_id);
        }
      } catch {
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  const readiness = dashboardData?.readiness_score?.overall || 0;
  const overallProgress = dashboardData?.overall_progress || 0;
  const targetCareer = selectedCareer?.career_name || selectedCareer?.name || null;
  const matchScore = selectedCareer?.match_score ? Math.round(selectedCareer.match_score * 100) : 0;

  const phases = dashboardData?.phases || {};
  const weeklyActions: string[] = [];
  if (phases.in_progress > 0) {
    weeklyActions.push("Continue your current learning phase");
  }
  if (phases.completed < phases.total) {
    weeklyActions.push("Complete the next phase in your roadmap");
  }
  if (!dashboardData?.assessment_completed) {
    weeklyActions.push("Take the career fit assessment");
  }
  if (!targetCareer) {
    weeklyActions.push("Choose a career to get started");
  } else if (recommendations.length === 0) {
    weeklyActions.push("Get your career recommendations");
  }

  const recentProgress = [
    { date: new Date().toISOString().split("T")[0], skills_mastered: phases.completed || 0, projects_completed: dashboardData?.projects?.completed || 0, assessment_score: Math.round(readiness) },
  ];

  return (
    <div className="max-w-6xl space-y-6">
      <DashboardHeader
        name={user?.name || "there"}
        overallProgress={overallProgress}
        careerReadiness={readiness}
      />

      <div className="grid md:grid-cols-2 gap-6">
        <CareerOverview
          targetCareer={targetCareer}
          matchScore={matchScore}
          readiness={readiness}
        />
        <SkillGapOverview gaps={selectedCareer?.skill_gaps || []} />
      </div>

      <WeeklyActions actions={weeklyActions} />

      <ProgressChart data={recentProgress} />
    </div>
  );
}
