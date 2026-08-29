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
import { cn } from "@/lib/utils";
import type { JobMatchResult, JobSkillMatch } from "@/types";

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

  const tone =
    alignment_percentage >= 70 ? "link" : alignment_percentage >= 40 ? "warn" : "err";

  return (
    <div className="space-y-5">
      <Card>
        <CardContent className="p-6 sm:p-8">
          <div className="text-center">
            <p className="font-mono text-xs uppercase tracking-wider text-mute">Job Alignment</p>
            <h2 className="mt-1 text-lg font-semibold text-ink">{job_title}</h2>
            <div
              className={cn(
                "mt-4 text-5xl font-semibold tracking-tight",
                tone === "link" && "text-link",
                tone === "warn" && "text-warn-deep",
                tone === "err" && "text-err-deep"
              )}
            >
              {alignment_percentage}%
            </div>
            <Progress value={alignment_percentage} className="mx-auto mt-4 h-2 max-w-md" />
            <div className="mt-4 flex flex-col items-center justify-center gap-1 text-sm text-body sm:flex-row sm:gap-6">
              <span>{matched_count} / {required_skills_count} required skills matched</span>
              <span className="hidden sm:inline text-hairline-strong">·</span>
              <span>{evidence_created} evidence records created</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-start gap-3 rounded-xl border border-link/20 bg-link-soft/40 p-4">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-link-deep" />
        <p className="text-sm text-link-deep">
          Evidence is only created for skills you already demonstrate. Missing skills are identified
          honestly — no false claims are made on your behalf.
        </p>
      </div>

      {strong_skills.length > 0 && (
        <SkillSection
          title="Strong"
          icon={<CheckCircle2 className="h-4 w-4 text-link" />}
          skills={strong_skills}
          markClassName="text-link"
          mark="✓"
        />
      )}

      {developing_skills.length > 0 && (
        <SkillSection
          title="Developing"
          icon={<AlertTriangle className="h-4 w-4 text-warn-deep" />}
          skills={developing_skills}
          markClassName="text-warn-deep"
          mark="△"
        />
      )}

      {missing_skills.length > 0 && (
        <SkillSection
          title="Missing"
          icon={<XCircle className="h-4 w-4 text-err" />}
          skills={missing_skills}
          markClassName="text-err"
          mark="○"
        />
      )}

      {not_demonstrated.length > 0 && (
        <SkillSection
          title="Not Demonstrated"
          icon={<HelpCircle className="h-4 w-4 text-mute" />}
          skills={not_demonstrated}
          markClassName="text-mute"
          mark="?"
        />
      )}

      {(top_gap || next_action) && (
        <Card className="border-ink/10 bg-canvas-soft">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <Target className="h-4 w-4" />
              Your Next Best Action
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {top_gap && (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-body">Top Gap:</span>
                <Badge variant="destructive">{top_gap}</Badge>
              </div>
            )}
            {next_action && (
              <div className="flex items-start gap-2 text-sm text-ink">
                <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-link" />
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
  mark,
  markClassName,
}: {
  title: string;
  icon: React.ReactNode;
  skills: JobSkillMatch[];
  mark: string;
  markClassName: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold text-ink">
          {icon}
          {title}
          <Badge variant="secondary" className="ml-1">{skills.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          {skills.map((skill, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-lg bg-canvas-soft px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <span className={cn("font-mono text-sm", markClassName)}>{mark}</span>
                <span className="text-sm font-medium text-ink">{skill.skill_name}</span>
                {skill.user_proficiency > 0 && (
                  <span className="text-xs text-mute">· {skill.user_proficiency}/5</span>
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
