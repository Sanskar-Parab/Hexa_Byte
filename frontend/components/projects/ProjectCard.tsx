"use client";

import { Clock, BarChart2, Play, CheckCircle2, RotateCcw } from "lucide-react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getDifficultyColor } from "@/lib/utils";
import { api } from "@/lib/api";
import { useState } from "react";

interface ProjectCardProps {
  project: any;
  onUpdate?: () => void;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  recommended: { label: "Not Started", color: "bg-slate-100 text-slate-700", icon: RotateCcw },
  in_progress: { label: "In Progress", color: "bg-blue-100 text-blue-700", icon: Play },
  completed: { label: "Completed", color: "bg-emerald-100 text-emerald-700", icon: CheckCircle2 },
};

export function ProjectCard({ project, onUpdate }: ProjectCardProps) {
  const router = useRouter();
  const [updating, setUpdating] = useState(false);
  const p = project.project || project;
  const matchPercent = Math.round(((project.match_score ?? project.composite_score) || 0) * 100);
  const status = project.status || "recommended";
  const projectId = project.id || project.project?.id;
  const isAI = project.is_ai_generated || project.type === "ai_generated";

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
      className="group relative z-0 hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5 cursor-pointer"
      onClick={handleClick}
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-semibold text-slate-900 group-hover:text-blue-700 transition-colors line-clamp-1">
            {p.title}
          </h3>
          <div className="flex items-center gap-2">
            {isAI && (
              <Badge className="bg-amber-100 text-amber-700 text-xs">AI</Badge>
            )}
            <Badge className={getDifficultyColor(p.difficulty)}>
              {p.difficulty}
            </Badge>
          </div>
        </div>

        <p className="text-sm text-slate-600 leading-relaxed mb-4 line-clamp-2">
          {p.description}
        </p>

        <div className="flex flex-wrap gap-2 mb-4">
          {(p.skills_developed || project.skills_targeted || []).slice(0, 4).map((skill: string) => (
            <Badge key={skill} variant="secondary" className="text-xs">
              {skill}
            </Badge>
          ))}
          {(p.skills_developed || project.skills_targeted || []).length > 4 && (
            <Badge variant="secondary" className="text-xs">
              +{(p.skills_developed || project.skills_targeted || []).length - 4} more
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-500 mb-4">
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span>{p.estimated_duration_weeks ? `${p.estimated_duration_weeks} weeks` : project.duration || "N/A"}</span>
          </div>
          {p.portfolio_value && (
            <div className="flex items-center gap-1.5">
              <BarChart2 className="h-3.5 w-3.5" />
              <span>{p.portfolio_value}</span>
            </div>
          )}
        </div>

        {matchPercent > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500">Relevance</span>
              <span className="font-semibold text-blue-600">{matchPercent}%</span>
            </div>
          </div>
        )}

        <div className="pt-3 border-t flex items-center justify-between">
          <Badge className={statusConfig.color}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {statusConfig.label}
          </Badge>
          <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
            {status === "recommended" && (
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs"
                onClick={(e) => handleStatusChange(e, "in_progress")}
                disabled={updating}
              >
                <Play className="h-3 w-3 mr-1" /> Start
              </Button>
            )}
            {status === "in_progress" && (
              <Button
                size="sm"
                className="h-7 text-xs bg-emerald-600 hover:bg-emerald-700"
                onClick={(e) => handleStatusChange(e, "completed")}
                disabled={updating}
              >
                <CheckCircle2 className="h-3 w-3 mr-1" /> Complete
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
