"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
  const { extraction, matched_skills, evidence_created, message } = result;

  const sections = [
    { label: "Skills", items: extraction.skills, icon: Lightbulb, color: "blue" },
    { label: "Experience", items: extraction.experience, icon: Briefcase, color: "emerald" },
    { label: "Education", items: extraction.education, icon: GraduationCap, color: "purple" },
    { label: "Projects", items: extraction.projects, icon: FolderOpen, color: "amber" },
    { label: "Certifications", items: extraction.certifications, icon: Award, color: "rose" },
    { label: "Technologies", items: extraction.technologies, icon: Wrench, color: "cyan" },
    { label: "Tools", items: extraction.tools, icon: Wrench, color: "slate" },
  ];

  return (
    <div className="space-y-6">
      <Card className="border-emerald-200 bg-emerald-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 mt-0.5" />
            <div>
              <p className="font-medium text-emerald-800">Resume Processed Successfully</p>
              <p className="text-sm text-emerald-700 mt-1">{message}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">Evidence, Not Proof</p>
              <p className="text-sm text-amber-700 mt-1">
                Resume mentions are <strong>evidence</strong> with MEDIUM confidence.
                They are NOT proof of expert proficiency.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {matched_skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Matched Skills (Evidence Created)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {matched_skills.map((skill, i) => (
                <Badge key={i} variant="secondary" className="bg-blue-50 text-blue-700 border-blue-200">
                  {skill.skill_name}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sections.map((section) => (
          section.items.length > 0 && (
            <Card key={section.label}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <section.icon className="h-4 w-4" />
                  {section.label}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {section.items.map((item, i) => (
                    <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                      <span className="text-slate-400 mt-1">-</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )
        ))}
      </div>
    </div>
  );
}
