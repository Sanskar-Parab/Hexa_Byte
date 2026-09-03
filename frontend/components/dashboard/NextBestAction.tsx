"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Zap,
  BookOpen,
  FolderKanban,
  FileText,
  Search,
  RotateCcw,
  CheckCircle,
  ArrowRight,
  Target,
  Briefcase,
  Compass,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonBlock } from "@/components/ui/loading-state";
import { api } from "@/lib/api";
import { NextBestAction } from "@/types";

const ACTION_ICONS: Record<string, React.ReactNode> = {
  ASSESS_SKILL: <BookOpen className="h-5 w-5" />,
  START_PHASE: <ArrowRight className="h-5 w-5" />,
  COMPLETE_PHASE: <CheckCircle className="h-5 w-5" />,
  BUILD_PROJECT: <FolderKanban className="h-5 w-5" />,
  UPLOAD_RESUME: <FileText className="h-5 w-5" />,
  ANALYZE_JOB: <Search className="h-5 w-5" />,
  RETAKE_ASSESSMENT: <RotateCcw className="h-5 w-5" />,
  IMPROVE_SKILL_FOR_PLACEMENT: <Target className="h-5 w-5" />,
  APPLY_OPPORTUNITIES: <Briefcase className="h-5 w-5" />,
  EXPLORE_RELEVANT_OPPORTUNITIES: <Compass className="h-5 w-5" />,
};

const ACTION_LABELS: Record<string, string> = {
  ASSESS_SKILL: "Assess This Skill",
  START_PHASE: "Start Phase",
  COMPLETE_PHASE: "Go to Roadmap",
  BUILD_PROJECT: "Start Project",
  UPLOAD_RESUME: "Upload Resume",
  ANALYZE_JOB: "Analyze a Job",
  RETAKE_ASSESSMENT: "Retake Assessment",
  IMPROVE_SKILL_FOR_PLACEMENT: "Build Toward This Skill",
  APPLY_OPPORTUNITIES: "Browse Opportunities",
  EXPLORE_RELEVANT_OPPORTUNITIES: "Explore Opportunities",
};

const ACTION_ROUTES: Record<string, (careerId?: string | null) => string> = {
  ASSESS_SKILL: () => "/skills",
  START_PHASE: (cid) => cid ? `/roadmap?career_id=${cid}` : "/roadmap",
  COMPLETE_PHASE: (cid) => cid ? `/roadmap?career_id=${cid}` : "/roadmap",
  BUILD_PROJECT: (cid) => cid ? `/projects?career_id=${cid}` : "/projects",
  UPLOAD_RESUME: () => "/skills",
  ANALYZE_JOB: () => "/careers",
  RETAKE_ASSESSMENT: () => "/assessment",
  IMPROVE_SKILL_FOR_PLACEMENT: () => "/projects",
  APPLY_OPPORTUNITIES: () => "/opportunities",
  EXPLORE_RELEVANT_OPPORTUNITIES: () => "/opportunities",
};

interface NextBestActionCardProps {
  careerId?: string | null;
}

export function NextBestActionCard({ careerId }: NextBestActionCardProps) {
  const router = useRouter();
  const [action, setAction] = useState<NextBestAction | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getNextBestAction(careerId || undefined)
      .then(setAction)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [careerId]);

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6 sm:p-8">
          <div className="flex gap-4">
            <SkeletonBlock className="h-12 w-12 shrink-0 rounded-full" />
            <div className="flex-1 space-y-3">
              <SkeletonBlock className="h-3 w-32" />
              <SkeletonBlock className="h-5 w-2/3" />
              <SkeletonBlock className="h-3 w-full" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!action || !action.action) {
    return (
      <EmptyState
        icon={Target}
        title="Your path starts here."
        description="Choose a target career and we'll build a roadmap around your current skills and gaps."
        actionLabel="Explore Careers"
        actionHref="/careers"
      />
    );
  }

  const icon = ACTION_ICONS[action.action] || <Zap className="h-5 w-5" />;
  const label = ACTION_LABELS[action.action] || "Take Action";
  const routeFn = ACTION_ROUTES[action.action];

  const handleAction = () => {
    if (routeFn) {
      router.push(routeFn(action.career_id));
    }
  };

  return (
    <Card className="overflow-hidden border-hairline">
      <CardContent className="p-6 sm:p-8">
        <div className="flex items-start gap-4 sm:gap-5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-ink text-white">
            {icon}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs uppercase tracking-wider text-mute">
                Next Best Action
              </span>
              {action.career_name && (
                <Badge variant="secondary" className="text-xs">
                  {action.career_name}
                </Badge>
              )}
            </div>
            <h3 className="mt-1.5 text-xl font-semibold tracking-tight text-ink">
              {action.title}
            </h3>
            <p className="mt-1.5 text-sm leading-relaxed text-body">
              <span className="font-medium text-ink">Why this? </span>
              {action.why}
            </p>

            {action.current && action.target && (
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <div className="rounded-lg bg-canvas-soft2 px-3 py-1.5 text-xs">
                  <span className="text-mute">Current: </span>
                  <span className="font-semibold text-ink">{action.current}</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-mute" />
                <div className="rounded-lg bg-link-soft px-3 py-1.5 text-xs">
                  <span className="text-link-deep/70">Target: </span>
                  <span className="font-semibold text-link-deep">{action.target}</span>
                </div>
              </div>
            )}

            <Button onClick={handleAction} className="mt-5">
              {label}
              <ArrowRight className="ml-2 h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
