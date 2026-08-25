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
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
};

const ACTION_ROUTES: Record<string, (careerId?: string | null) => string> = {
  ASSESS_SKILL: () => "/skills",
  START_PHASE: (cid) => cid ? `/roadmap?career_id=${cid}` : "/roadmap",
  COMPLETE_PHASE: (cid) => cid ? `/roadmap?career_id=${cid}` : "/roadmap",
  BUILD_PROJECT: (cid) => cid ? `/projects?career_id=${cid}` : "/projects",
  UPLOAD_RESUME: () => "/skills",
  ANALYZE_JOB: () => "/careers",
  RETAKE_ASSESSMENT: () => "/assessment",
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
        <CardContent className="p-6">
          <div className="animate-pulse flex space-x-4">
            <div className="rounded-full bg-slate-200 h-12 w-12" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-slate-200 rounded w-1/3" />
              <div className="h-3 bg-slate-200 rounded w-2/3" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!action || !action.action) {
    return null;
  }

  const icon = ACTION_ICONS[action.action] || <Zap className="h-5 w-5" />;
  const routeFn = ACTION_ROUTES[action.action];

  const handleAction = () => {
    if (routeFn) {
      router.push(routeFn(action.career_id));
    }
  };

  return (
    <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50">
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 p-3 rounded-full bg-blue-100 text-blue-700">
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wide text-blue-600">
                Next Best Action
              </span>
              {action.career_name && (
                <Badge variant="secondary" className="text-xs">
                  {action.career_name}
                </Badge>
              )}
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-1">
              {action.title}
            </h3>
            <p className="text-sm text-slate-600 mb-3">{action.why}</p>

            {action.current && action.target && (
              <div className="flex items-center gap-3 mb-3">
                <div className="text-xs">
                  <span className="text-slate-500">Current: </span>
                  <span className="font-semibold text-slate-700">
                    {action.current}
                  </span>
                </div>
                <ArrowRight className="h-3 w-3 text-slate-400" />
                <div className="text-xs">
                  <span className="text-slate-500">Target: </span>
                  <span className="font-semibold text-blue-700">
                    {action.target}
                  </span>
                </div>
              </div>
            )}

            <Button onClick={handleAction} size="sm" className="mt-1">
              Start Assessment
              <ArrowRight className="ml-2 h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
