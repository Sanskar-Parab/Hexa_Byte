"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ArrowRight,
  Info,
  Target,
} from "lucide-react";
import type { JobMatchResult } from "@/types";

interface JobMatchResultsProps {
  result: JobMatchResult;
}

export function JobMatchResults({ result }: JobMatchResultsProps) {
  const {
    job_title,
    alignment_percentage,
    strong_skills,
    developing_skills,
    missing_skills,
    not_demonstrated,
    top_gap,
    next_action,
    evidence_created,
    required_skills_count,
    matched_count,
  } = result;

  const alignmentColor =
    alignment_percentage >= 70 ? "text-emerald-600" :
    alignment_percentage >= 40 ? "text-amber-600" :
    "text-rose-600";

  const alignmentBg =
    alignment_percentage >= 70 ? "bg-emerald-50" :
    alignment_percentage >= 40 ? "bg-amber-50" :
    "bg-rose-50";

  return (
    <div className="space-y-6">
      <Card className={`${alignmentBg} border-2`}>
        <CardContent className="p-6">
          <div className="text-center space-y-3">
            <p className="text-sm font-medium text-slate-600">Job Match Analysis</p>
            <h2 className="text-xl font-bold text-slate-900">{job_title}</h2>
            <div className={`text-5xl font-bold ${alignmentColor}`}>
              {alignment_percentage}%
            </div>
            <p className="text-sm text-slate-600">alignment</p>
            <Progress value={alignment_percentage} className="h-3 max-w-md mx-auto" />
            <div className="flex justify-center gap-6 text-sm text-slate-600 pt-2">
              <span>{matched_count} / {required_skills_count} required skills matched</span>
              <span>{evidence_created} evidence records created</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <p className="font-medium text-blue-800">Job Analysis Creates Evidence Only</p>
              <p className="text-sm text-blue-700 mt-1">
                Evidence is created only for skills you <strong>already have</strong>.
                Missing skills are identified but no false claims are made.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {strong_skills.length > 0 && (
        <SkillSection
          title="Strong Skills"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
          skills={strong_skills}
          badgeClass="bg-emerald-50 text-emerald-700 border-emerald-200"
        />
      )}

      {developing_skills.length > 0 && (
        <SkillSection
          title="Developing Skills"
          icon={<AlertTriangle className="h-5 w-5 text-amber-600" />}
          skills={developing_skills}
          badgeClass="bg-amber-50 text-amber-700 border-amber-200"
        />
      )}

      {missing_skills.length > 0 && (
        <SkillSection
          title="Missing Skills"
          icon={<XCircle className="h-5 w-5 text-rose-600" />}
          skills={missing_skills}
          badgeClass="bg-rose-50 text-rose-700 border-rose-200"
        />
      )}

      {not_demonstrated.length > 0 && (
        <SkillSection
          title="Not Demonstrated"
          icon={<HelpCircle className="h-5 w-5 text-slate-500" />}
          skills={not_demonstrated}
          badgeClass="bg-slate-50 text-slate-700 border-slate-200"
        />
      )}

      {(top_gap || next_action) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Target className="h-5 w-5 text-blue-600" />
              Recommendation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {top_gap && (
              <div className="flex items-start gap-2">
                <span className="text-sm font-medium text-slate-700">Top Gap:</span>
                <Badge variant="outline" className="bg-rose-50 text-rose-700">{top_gap}</Badge>
              </div>
            )}
            {next_action && (
              <div className="flex items-center gap-2 text-sm text-slate-700">
                <ArrowRight className="h-4 w-4 text-blue-600" />
                <span className="font-medium">Next Action:</span>
                <span>{next_action}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function SkillSection({
  title,
  icon,
  skills,
  badgeClass,
}: {
  title: string;
  icon: React.ReactNode;
  skills: any[];
  badgeClass: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          {icon}
          {title}
          <Badge variant="secondary" className="ml-1">{skills.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {skills.map((skill, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-2 rounded-lg bg-slate-50"
            >
              <div className="flex-1">
                <span className="font-medium text-sm text-slate-800">{skill.skill_name}</span>
                {skill.user_proficiency > 0 && (
                  <span className="ml-2 text-xs text-slate-500">
                    Proficiency: {skill.user_proficiency}/5
                  </span>
                )}
              </div>
              {skill.evidence_count > 0 && (
                <Badge variant="outline" className="text-xs">
                  {skill.evidence_count} evidence
                </Badge>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
