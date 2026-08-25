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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  recommended: { label: "Not Started", color: "bg-slate-100 text-slate-700", icon: RotateCcw },
  in_progress: { label: "In Progress", color: "bg-blue-100 text-blue-700", icon: Play },
  completed: { label: "Completed", color: "bg-emerald-100 text-emerald-700", icon: CheckCircle2 },
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
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="max-w-4xl mx-auto py-10">
        <Button variant="ghost" onClick={() => router.back()} className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Projects
        </Button>
        <div className="text-center py-20">
          <h2 className="text-xl font-semibold text-slate-900">Project not found</h2>
          <p className="text-slate-600 mt-2">The project you're looking for doesn't exist.</p>
        </div>
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

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            {isAI && (
              <Badge className="bg-amber-100 text-amber-700">
                <Sparkles className="h-3 w-3 mr-1" /> AI Generated
              </Badge>
            )}
            <Badge className={getDifficultyColor(project.difficulty)}>
              {project.difficulty}
            </Badge>
            <Badge className={statusConfig.color}>
              <StatusIcon className="h-3 w-3 mr-1" />
              {statusConfig.label}
            </Badge>
          </div>
          <h1 className="text-3xl font-bold text-slate-900">{project.title}</h1>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <p className="text-slate-700 leading-relaxed">{project.description}</p>
          {isAI && project.why_this_project && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800 italic">
                <strong>Why this project:</strong> {project.why_this_project}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-600" />
              Duration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold text-slate-900">
              {project.estimated_duration_weeks
                ? `${project.estimated_duration_weeks} weeks`
                : project.duration || "N/A"}
            </p>
          </CardContent>
        </Card>

        {project.portfolio_value && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <BarChart2 className="h-5 w-5 text-purple-600" />
                Portfolio Value
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold text-slate-900">{project.portfolio_value}</p>
            </CardContent>
          </Card>
        )}
      </div>

      {project.expected_outcome && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Target className="h-5 w-5 text-emerald-600" />
              Expected Outcome
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-700">{project.expected_outcome}</p>
          </CardContent>
        </Card>
      )}

      {skills.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart2 className="h-5 w-5 text-amber-600" />
              Skills
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
            <CardTitle className="text-lg flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-indigo-600" />
              Learning Objectives
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {project.learning_objectives.map((obj, idx) => (
                <li key={idx} className="flex items-start gap-2 text-slate-700">
                  <CheckCircle2 className="h-4 w-4 text-indigo-500 mt-0.5 shrink-0" />
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
            <CardTitle className="text-lg flex items-center gap-2">
              <Package className="h-5 w-5 text-rose-600" />
              Deliverables
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {project.deliverables.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2 text-slate-700">
                  <CheckCircle2 className="h-4 w-4 text-rose-500 mt-0.5 shrink-0" />
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
            <CardTitle className="text-lg flex items-center gap-2">
              <ClipboardCheck className="h-5 w-5 text-teal-600" />
              Completion Criteria
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {project.completion_criteria.map((criteria, idx) => (
                <li key={idx} className="flex items-start gap-2 text-slate-700">
                  <CheckCircle2 className="h-4 w-4 text-teal-500 mt-0.5 shrink-0" />
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
            <CardTitle className="text-lg flex items-center gap-2">
              <Calendar className="h-5 w-5 text-slate-600" />
              Progress Timeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {project.started_at && (
                <div className="flex items-center gap-3">
                  <div className="h-3 w-3 rounded-full bg-blue-500" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">Started</p>
                    <p className="text-xs text-slate-500">
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
                  <div className="h-3 w-3 rounded-full bg-emerald-500" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">Completed</p>
                    <p className="text-xs text-slate-500">
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

      <Card className="bg-slate-50">
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Project Actions</h3>
          <div className="flex gap-3">
            {project.status === "recommended" && (
              <Button
                onClick={() => handleStatusChange("in_progress")}
                disabled={updating}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Play className="h-4 w-4 mr-2" /> Start Project
              </Button>
            )}
            {project.status === "in_progress" && (
              <Button
                onClick={() => handleStatusChange("completed")}
                disabled={updating}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                <CheckCircle2 className="h-4 w-4 mr-2" /> Mark as Completed
              </Button>
            )}
            {project.status === "completed" && (
              <Button
                onClick={() => handleStatusChange("in_progress")}
                disabled={updating}
                variant="outline"
              >
                <RotateCcw className="h-4 w-4 mr-2" /> Reopen Project
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
