"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Clock,
  BarChart2,
  CheckCircle2,
  Play,
  RotateCcw,
  Target,
  BookOpen,
  Package,
  ClipboardCheck,
  Sparkles,
  Calendar,
  Circle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { getDifficultyColor } from "@/lib/utils";

interface ProjectDetail {
  type: "database" | "ai_generated";
  id: string;
  project_id: string;
  title: string;
  description: string;
  difficulty: string;
  career_id: string;
  status: string;
  skills_developed?: string[];
  expected_outcome?: string;
  estimated_duration_weeks?: number;
  portfolio_value?: string;
  why_this_project?: string;
  skills_practiced?: string[];
  skills_targeted?: string[];
  duration?: string;
  learning_objectives?: string[];
  deliverables?: string[];
  completion_criteria?: string[];
  started_at?: string;
  completed_at?: string;
}

const STATUS_CONFIG: Record<string, { label: string; className: string; icon: typeof Circle }> = {
  recommended: { label: "Not Started", className: "bg-canvas-soft2 text-mute", icon: RotateCcw },
  in_progress: { label: "In Progress", className: "bg-warn-soft text-warn-deep", icon: Play },
  completed: { label: "Completed", className: "bg-link-soft text-link-deep", icon: CheckCircle2 },
};

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    const loadProject = async () => {
      try {
        const data = await api.getProjectDetail(params.id as string);
        setProject(data);
      } catch {
      } finally {
        setLoading(false);
      }
    };
    loadProject();
  }, [params.id]);

  const handleStatusChange = async (newStatus: string) => {
    if (!project || updating) return;
    setUpdating(true);
    try {
      await api.updateProjectStatus(project.id, newStatus);
      setProject({ ...project, status: newStatus });
    } catch {
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return <LoadingState message="Loading project..." />;
  }

  if (!project) {
    return (
      <div className="max-w-4xl mx-auto py-10">
        <Button variant="ghost" onClick={() => router.back()} className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Projects
        </Button>
        <EmptyState
          title="Project not found"
          description="The project you're looking for doesn't exist or may have been removed."
        />
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[project.status] || STATUS_CONFIG.recommended;
  const StatusIcon = statusConfig.icon;
  const isAI = project.type === "ai_generated";
  const skills = isAI
    ? [...(project.skills_practiced || []), ...(project.skills_targeted || [])]
    : project.skills_developed || [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Button variant="ghost" onClick={() => router.back()} className="mb-2">
        <ArrowLeft className="h-4 w-4 mr-2" /> Back to Projects
      </Button>

      <div>
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {isAI && (
            <Badge variant="violet">
              <Sparkles className="h-3 w-3" /> AI Generated
            </Badge>
          )}
          <Badge className={getDifficultyColor(project.difficulty)}>{project.difficulty}</Badge>
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${statusConfig.className}`}>
            <StatusIcon className="h-3 w-3" />
            {statusConfig.label}
          </span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">{project.title}</h1>
      </div>

      <Card>
        <CardContent className="p-6">
          <p className="leading-relaxed text-body">{project.description}</p>
          {isAI && project.why_this_project && (
            <div className="mt-4 flex gap-2 rounded-lg bg-canvas-soft p-4">
              <Target className="mt-0.5 h-4 w-4 shrink-0 text-link" />
              <p className="text-sm leading-relaxed text-body">
                <strong className="text-ink">Why this project — </strong>
                {project.why_this_project}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <Clock className="h-4 w-4 text-mute" />
              Duration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold tracking-tight text-ink">
              {project.estimated_duration_weeks ? `${project.estimated_duration_weeks} weeks` : project.duration || "N/A"}
            </p>
          </CardContent>
        </Card>

        {project.portfolio_value && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
                <BarChart2 className="h-4 w-4 text-mute" />
                Portfolio Value
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold tracking-tight text-ink">{project.portfolio_value}</p>
            </CardContent>
          </Card>
        )}
      </div>

      {project.expected_outcome && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <Target className="h-4 w-4 text-mute" />
              Expected Outcome
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-body">{project.expected_outcome}</p>
          </CardContent>
        </Card>
      )}

      {skills.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <BarChart2 className="h-4 w-4 text-mute" />
              Skills Targeted
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {skills.map((skill) => (
                <Badge key={skill} variant="secondary">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {isAI && project.learning_objectives && project.learning_objectives.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <BookOpen className="h-4 w-4 text-mute" />
              Learning Objectives
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {project.learning_objectives.map((obj, idx) => (
                <li key={idx} className="flex items-start gap-2 text-body">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-link" />
                  {obj}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {isAI && project.deliverables && project.deliverables.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <Package className="h-4 w-4 text-mute" />
              Expected Evidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {project.deliverables.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2 text-body">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-link" />
                  {item}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {isAI && project.completion_criteria && project.completion_criteria.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <ClipboardCheck className="h-4 w-4 text-mute" />
              Completion Criteria
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {project.completion_criteria.map((criteria, idx) => (
                <li key={idx} className="flex items-start gap-2 text-body">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-link" />
                  {criteria}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {(project.started_at || project.completed_at) && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <Calendar className="h-4 w-4 text-mute" />
              Progress Timeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {project.started_at && (
                <div className="flex items-center gap-3">
                  <div className="h-2.5 w-2.5 rounded-full bg-warn" />
                  <div>
                    <p className="text-sm font-medium text-ink">Started</p>
                    <p className="text-xs text-mute">
                      {new Date(project.started_at).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>
              )}
              {project.completed_at && (
                <div className="flex items-center gap-3">
                  <div className="h-2.5 w-2.5 rounded-full bg-link" />
                  <div>
                    <p className="text-sm font-medium text-ink">Completed</p>
                    <p className="text-xs text-mute">
                      {new Date(project.completed_at).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="bg-canvas-soft">
        <CardContent className="p-6">
          <h3 className="mb-4 text-base font-semibold text-ink">Project Actions</h3>
          <div className="flex gap-3">
            {project.status === "recommended" && (
              <Button onClick={() => handleStatusChange("in_progress")} disabled={updating}>
                <Play className="h-4 w-4 mr-2" /> Start Project
              </Button>
            )}
            {project.status === "in_progress" && (
              <Button onClick={() => handleStatusChange("completed")} disabled={updating}>
                <CheckCircle2 className="h-4 w-4 mr-2" /> Mark as Completed
              </Button>
            )}
            {project.status === "completed" && (
              <Button onClick={() => handleStatusChange("in_progress")} disabled={updating} variant="outline">
                <RotateCcw className="h-4 w-4 mr-2" /> Reopen Project
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
