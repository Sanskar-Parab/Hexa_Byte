"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Map, CheckCircle2, CircleDot, Circle, FileText, FolderKanban, Brain } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { CareerOverview } from "@/components/dashboard/CareerOverview";
import { SkillGapOverview } from "@/components/dashboard/SkillGapOverview";
import { WeeklyActions } from "@/components/dashboard/WeeklyActions";
import { ProgressChart } from "@/components/dashboard/ProgressChart";
import { NextBestActionCard } from "@/components/dashboard/NextBestAction";
import { OpportunitiesForYou } from "@/components/dashboard/OpportunitiesForYou";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CardSkeleton, SkeletonBlock } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";

export default function DashboardPage() {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [selectedCareer, setSelectedCareer] = useState<any>(null);
  const [skillGaps, setSkillGaps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedCareerId = localStorage.getItem("selectedCareerId");

    const loadData = async () => {
      try {
        const [dashData, recs] = await Promise.all([
          api.getDashboard(storedCareerId || undefined).catch(() => null),
          api.getStoredRecommendations().catch(() => []),
        ]);
        setDashboardData(dashData);
        setRecommendations(recs);

        let activeCareer = null;
        if (storedCareerId) {
          const matched = recs.find((r: any) => String(r.career_id) === String(storedCareerId));
          if (matched) {
            activeCareer = matched;
          } else {
            activeCareer = await api.getCareerDetail(storedCareerId).catch(() => null);
          }
        } else if (recs.length > 0) {
          activeCareer = recs[0];
          localStorage.setItem("selectedCareerId", recs[0].career_id);
        }
        setSelectedCareer(activeCareer);

        const activeCareerId = activeCareer?.career_id || activeCareer?.id || storedCareerId;
        if (activeCareerId) {
          const gapResult = await api.analyzeSkillGap(activeCareerId).catch(() => null);
          if (gapResult && gapResult.gaps) {
            setSkillGaps(gapResult.gaps);
          }
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
      <div className="max-w-6xl space-y-6">
        <div className="space-y-3">
          <SkeletonBlock className="h-3 w-40" />
          <SkeletonBlock className="h-9 w-72" />
          <p className="text-sm text-mute">Analyzing your skills...</p>
        </div>
        <CardSkeleton />
        <div className="grid gap-6 md:grid-cols-2">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  const readiness = dashboardData?.readiness_score?.career_readiness
    ?? dashboardData?.readiness_score?.overall
    ?? 0;
  const overallProgress = dashboardData?.overall_progress || 0;
  const targetCareer = selectedCareer?.career_name || selectedCareer?.name || null;
  const matchScore = selectedCareer?.match_score ? Math.round(selectedCareer.match_score * 100) : 0;

  const phases = dashboardData?.phases || {};
  const phaseItems: any[] = phases.items || [];
  const currentPhaseNumber = Math.min(phases.total || 0, (phases.completed || 0) + 1);

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

  const recentProgress = dashboardData?.recent_progress || [
    { date: new Date().toISOString().split("T")[0], skills_mastered: phases.completed || 0, projects_completed: dashboardData?.projects?.completed || 0, assessment_score: Math.round(readiness) },
  ];

  const evidenceRows: { icon: any; label: string; done: boolean }[] = [];
  if (dashboardData?.assessment_completed) {
    evidenceRows.push({ icon: Brain, label: "AI Assessment", done: true });
  }
  phaseItems
    .filter((p) => p.status === "completed")
    .forEach((p) => evidenceRows.push({ icon: CheckCircle2, label: `Roadmap Phase: ${p.title}`, done: true }));
  const completedProjects = dashboardData?.projects?.completed || 0;
  if (completedProjects > 0) {
    evidenceRows.push({ icon: FolderKanban, label: `${completedProjects} Project${completedProjects > 1 ? "s" : ""} Completed`, done: true });
  }

  return (
    <div className="max-w-6xl space-y-6">
      <DashboardHeader
        name={user?.name || "there"}
        overallProgress={overallProgress}
        careerReadiness={readiness}
      />

      <NextBestActionCard careerId={selectedCareer?.career_id} />

      <div className="grid gap-6 md:grid-cols-2">
        <CareerOverview
          targetCareer={targetCareer}
          matchScore={matchScore}
          readiness={readiness}
        />
        <SkillGapOverview gaps={skillGaps.length > 0 ? skillGaps : (selectedCareer?.skill_gaps || [])} />
      </div>

      <OpportunitiesForYou careerId={selectedCareer?.career_id} />

      {phases.total > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <Map className="h-4 w-4 text-mute" />
              Roadmap — Phase {currentPhaseNumber} of {phases.total}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              {phaseItems.map((phase, i) => {
                const Icon = phase.status === "completed" ? CheckCircle2 : phase.status === "in_progress" ? CircleDot : Circle;
                return (
                  <div key={phase.phase_id || i} className="flex flex-1 items-center last:flex-none">
                    <div className="flex flex-col items-center gap-1.5">
                      <Icon
                        className={
                          phase.status === "completed"
                            ? "h-5 w-5 text-link"
                            : phase.status === "in_progress"
                            ? "h-5 w-5 text-warn"
                            : "h-5 w-5 text-hairline-strong"
                        }
                      />
                      <span className="max-w-[80px] truncate text-center text-[11px] text-mute">{phase.title}</span>
                    </div>
                    {i < phaseItems.length - 1 && (
                      <div className={`mx-1 h-px flex-1 ${phase.status === "completed" ? "bg-link" : "bg-hairline"}`} />
                    )}
                  </div>
                );
              })}
            </div>
            <Link href="/roadmap" className="mt-4 inline-block text-xs font-medium text-link hover:underline">
              View full roadmap &rarr;
            </Link>
          </CardContent>
        </Card>
      ) : (
        <EmptyState
          icon={Map}
          title="Your roadmap hasn't started"
          description="Generate a roadmap from a target career to see your phase-by-phase path here."
          actionLabel="Explore Careers"
          actionHref="/careers"
        />
      )}

      {evidenceRows.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <FileText className="h-4 w-4 text-mute" />
              Recent Evidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2.5">
              {evidenceRows.map((row, i) => {
                const Icon = row.icon;
                return (
                  <li key={i} className="flex items-center gap-2.5 text-sm">
                    <Icon className="h-4 w-4 shrink-0 text-link" />
                    <span className="text-body">{row.label}</span>
                    <span className="ml-auto text-xs font-medium text-link-deep">✓ Completed</span>
                  </li>
                );
              })}
            </ul>
          </CardContent>
        </Card>
      )}

      <WeeklyActions actions={weeklyActions} />

      <ProgressChart data={recentProgress} />
    </div>
  );
}
