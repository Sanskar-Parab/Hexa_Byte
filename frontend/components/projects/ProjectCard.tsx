"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Clock, Sparkles, Play, CheckCircle2, Circle, Target } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getDifficultyColor } from "@/lib/utils";
import { api } from "@/lib/api";

interface ProjectCardProps {
  project: any;
  onUpdate?: () => void;
}

const STATUS_CONFIG: Record<string, { label: string; className: string; icon: typeof Circle }> = {
  recommended: { label: "Not Started", className: "bg-canvas-soft2 text-mute", icon: Circle },
  in_progress: { label: "In Progress", className: "bg-warn-soft text-warn-deep", icon: Play },
  completed: { label: "Completed", className: "bg-link-soft text-link-deep", icon: CheckCircle2 },
};

export function ProjectCard({ project, onUpdate }: ProjectCardProps) {
  const router = useRouter();
  const [updating, setUpdating] = useState(false);
  const p = project.project || project;
  const matchPercent = Math.round(((project.match_score ?? project.composite_score) || 0) * 100);
  const status = project.status || "recommended";
  const projectId = project.id || project.project?.id;
  const isAI = project.is_ai_generated || project.type === "ai_generated";
  const skills: string[] = p.skills_developed || project.skills_targeted || project.covers_skills || [];
  const whyThisProject: string | undefined =
    project.why_this_project ||
    (project.gap_skills_covered?.length
      ? `Closes your gap in ${project.gap_skills_covered.slice(0, 2).join(" and ")}.`
      : undefined);

  const statusConfig = STATUS_CONFIG[status] || STATUS_CONFIG.recommended;
  const StatusIcon = statusConfig.icon;

  const handleStatusChange = async (e: React.MouseEvent, newStatus: string) => {
    e.stopPropagation();
    if (updating) return;
    setUpdating(true);
    try {
      await api.updateProjectStatus(projectId, newStatus);
      onUpdate?.();
    } catch (err) {
      console.error("Failed to update project status:", err);
    } finally {
      setUpdating(false);
    }
  };

  const handleClick = () => {
    router.push(`/projects/${projectId}`);
  };

  return (
    <Card
      className="group relative z-0 cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover"
      onClick={handleClick}
    >
      <CardContent className="flex h-full flex-col p-6">
        <div className="flex items-start justify-between gap-2 mb-3">
          <h3 className="line-clamp-1 text-lg font-semibold tracking-tight text-ink transition-colors group-hover:text-link">
            {p.title}
          </h3>
          <div className="flex shrink-0 items-center gap-2">
            {isAI && (
              <Badge variant="violet" className="text-[10px] font-mono uppercase tracking-wide">
                <Sparkles className="h-3 w-3" /> AI
              </Badge>
            )}
            <Badge className={getDifficultyColor(p.difficulty)}>{p.difficulty}</Badge>
          </div>
        </div>

        <p className="mb-4 line-clamp-2 text-sm leading-relaxed text-body">{p.description}</p>

        {skills.length > 0 && (
          <div className="mb-4">
            <p className="mb-1.5 font-mono text-[10px] uppercase tracking-wide text-mute">Targets</p>
            <div className="flex flex-wrap gap-1.5">
              {skills.slice(0, 4).map((skill: string) => (
                <Badge key={skill} variant="secondary" className="text-xs">
                  {skill}
                </Badge>
              ))}
              {skills.length > 4 && (
                <Badge variant="secondary" className="text-xs">
                  +{skills.length - 4} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {whyThisProject && (
          <div className="mb-4 flex items-start gap-2 rounded-lg bg-canvas-soft px-3 py-2">
            <Target className="mt-0.5 h-3.5 w-3.5 shrink-0 text-link" />
            <p className="text-xs leading-relaxed text-body">{whyThisProject}</p>
          </div>
        )}

        <div className="mb-4 flex items-center gap-4 text-xs text-mute">
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span>{p.estimated_duration_weeks ? `${p.estimated_duration_weeks} weeks` : project.duration || "N/A"}</span>
          </div>
          {matchPercent > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-link">{matchPercent}%</span>
              <span>relevance</span>
            </div>
          )}
        </div>

        <div className="mt-auto flex items-center justify-between border-t border-hairline pt-3">
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${statusConfig.className}`}>
            <StatusIcon className="h-3 w-3" />
            {statusConfig.label}
          </span>
          <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
            {status === "recommended" && (
              <Button size="sm" variant="outline" className="h-7 text-xs" onClick={(e) => handleStatusChange(e, "in_progress")} disabled={updating}>
                <Play className="h-3 w-3 mr-1" /> Start Project
              </Button>
            )}
            {status === "in_progress" && (
              <Button size="sm" className="h-7 text-xs" onClick={(e) => handleStatusChange(e, "completed")} disabled={updating}>
                <CheckCircle2 className="h-3 w-3 mr-1" /> Complete
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
