"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ConfidenceBadge } from "@/components/ui/status-badge";
import {
  CheckCircle2,
  Briefcase,
  GraduationCap,
  FolderOpen,
  Award,
  Wrench,
  Lightbulb,
  Info,
} from "lucide-react";
import type { ResumeUploadResult } from "@/types";

interface ResumeResultsProps {
  result: ResumeUploadResult;
}

export function ResumeResults({ result }: ResumeResultsProps) {
  const { extraction, matched_skills, message } = result;

  const sections = [
    { label: "Skills Detected", items: extraction.skills, icon: Lightbulb },
    { label: "Experience", items: extraction.experience, icon: Briefcase },
    { label: "Education", items: extraction.education, icon: GraduationCap },
    { label: "Projects Detected", items: extraction.projects, icon: FolderOpen },
    { label: "Certifications", items: extraction.certifications, icon: Award },
    { label: "Technologies", items: extraction.technologies, icon: Wrench },
    { label: "Tools", items: extraction.tools, icon: Wrench },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3 rounded-xl border border-link/20 bg-link-soft/40 p-4">
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-link-deep" />
        <div>
          <p className="text-sm font-medium text-link-deep">Resume processed successfully</p>
          <p className="mt-1 text-sm text-body">{message}</p>
        </div>
      </div>

      {matched_skills.length > 0 && (
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-base font-semibold text-ink">Matched Skills (Evidence Created)</CardTitle>
            <ConfidenceBadge confidence="medium" />
          </CardHeader>
          <CardContent>
            <div className="flex items-start gap-2 rounded-lg bg-canvas-soft p-3 mb-4 text-xs text-body">
              <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-mute" />
              We do not automatically claim expert proficiency from a resume — these mentions are
              recorded as medium-confidence evidence only.
            </div>
            <div className="flex flex-wrap gap-2">
              {matched_skills.map((skill, i) => (
                <Badge key={i} variant="secondary">
                  {skill.skill_name}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {sections.map(
          (section) =>
            section.items.length > 0 && (
              <Card key={section.label}>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm font-medium text-ink">
                    <section.icon className="h-4 w-4 text-mute" />
                    {section.label}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1.5">
                    {section.items.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-body">
                        <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-mute" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )
        )}
      </div>
    </div>
  );
}
