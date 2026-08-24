"use client";

import { Clock, BarChart2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getDifficultyColor } from "@/lib/utils";
import { RecommendedProject } from "@/types";

interface ProjectCardProps {
  project: RecommendedProject;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const p = project.project;
  const matchPercent = Math.round((project.match_score || 0) * 100);

  return (
    <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-semibold text-slate-900 group-hover:text-blue-700 transition-colors">
            {p.title}
          </h3>
          <Badge className={getDifficultyColor(p.difficulty)}>
            {p.difficulty}
          </Badge>
        </div>

        <p className="text-sm text-slate-600 leading-relaxed mb-4 line-clamp-2">
          {p.description}
        </p>

        <div className="flex flex-wrap gap-2 mb-4">
          {p.skills_developed.map((skill) => (
            <Badge key={skill} variant="secondary" className="text-xs">
              {skill}
            </Badge>
          ))}
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span>{p.estimated_duration_weeks} weeks</span>
          </div>
          <div className="flex items-center gap-1.5">
            <BarChart2 className="h-3.5 w-3.5" />
            <span>{p.portfolio_value}</span>
          </div>
        </div>

        {matchPercent > 0 && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500">Relevance</span>
              <span className="font-semibold text-blue-600">{matchPercent}%</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
