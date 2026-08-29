"use client";

import { CheckCircle2, Circle, BookOpen, AlertTriangle, Zap, Route } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfidenceBadge } from "@/components/ui/status-badge";
import { SkillGapChart } from "@/components/career/SkillGapChart";
import { SkillDetail, UserSkillBrief } from "@/types";

interface CareerDetailProps {
  career: {
    career_id: string;
    career_name: string;
    match_score: number;
    confidence: string;
    why_it_matches: string[];
    strengths: string[];
    skill_gaps: string[];
    biggest_blocker?: string | null;
    recommended_action?: string | null;
  };
  careerInfo?: {
    description?: string;
    required_skills?: string[];
    learning_sequence?: any[];
    related_careers?: string[];
  };
  intelligence?: {
    skill_details?: SkillDetail[];
    user_current_skills?: UserSkillBrief[];
  };
}

export function CareerDetail({ career, careerInfo, intelligence }: CareerDetailProps) {
  const scorePercent = Math.round(career.match_score * 100);
  const skillDetails = intelligence?.skill_details || [];
  const userCurrentSkills = intelligence?.user_current_skills || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-hairline bg-canvas p-6 shadow-card">
        <p className="font-mono text-xs uppercase tracking-wider text-mute mb-2">Career Intelligence</p>
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <h1 className="text-2xl font-semibold tracking-tight text-ink">{career.career_name}</h1>
          <span className="rounded-full bg-ink px-3 py-1 text-sm font-bold text-white">{scorePercent}% MATCH</span>
          <ConfidenceBadge confidence={career.confidence} />
        </div>
        {careerInfo?.description && (
          <p className="max-w-2xl text-sm leading-relaxed text-body">{careerInfo.description}</p>
        )}
      </div>

      {/* Strengths / Gaps */}
      <div className="grid gap-6 sm:grid-cols-2">
        {career.strengths && career.strengths.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Your Strengths</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {career.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-body">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-link" />
                    {s}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {career.skill_gaps && career.skill_gaps.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Your Gaps</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {career.skill_gaps.map((skill, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-body">
                    <Circle className="mt-1 h-2.5 w-2.5 shrink-0 fill-hairline-strong text-hairline-strong" />
                    {skill}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Requirements table */}
      {skillDetails.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Career Requirements</CardTitle>
          </CardHeader>
          <CardContent>
            <SkillGapChart skillDetails={skillDetails} />
          </CardContent>
        </Card>
      )}

      {/* Why this career */}
      {career.why_it_matches && career.why_it_matches.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Why This Career?</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {career.why_it_matches.map((reason, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-body">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-link" />
                  {reason}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Biggest blocker */}
      {career.biggest_blocker && (
        <Card className="border-warn-soft bg-warn-soft/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-5 w-5 text-warn-deep" />
              Biggest Blocker
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-semibold text-ink">{career.biggest_blocker}</p>
            <p className="mt-1 text-xs text-mute">
              This is the highest-priority skill gap for this career. Focus on developing it first.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Next best action */}
      {career.recommended_action && (
        <Card className="border-ink bg-ink text-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base text-white">
              <Zap className="h-5 w-5 text-cyan" />
              Your Next Best Action
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-white/90">{career.recommended_action}</p>
          </CardContent>
        </Card>
      )}

      {userCurrentSkills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Your Current Skills</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {userCurrentSkills.map((skill, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 rounded-full border border-hairline bg-canvas-soft px-3 py-1 text-sm text-body"
                >
                  {skill.name} ({skill.proficiency}/5)
                  <ConfidenceBadge confidence={skill.confidence} className="text-[9px]" />
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {careerInfo?.required_skills && careerInfo.required_skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Required Skills</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {careerInfo.required_skills.map((skill) => (
                <Badge key={skill} variant="secondary">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {careerInfo?.learning_sequence && careerInfo.learning_sequence.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BookOpen className="h-5 w-5 text-link" />
              Learning Pathway
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-3">
              {careerInfo.learning_sequence.map((step: any, i: number) => (
                <li key={i} className="flex items-start gap-3">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-canvas-soft2 text-xs font-bold text-ink">
                    {i + 1}
                  </div>
                  <div>
                    <span className="text-sm font-medium text-ink">{step.title}</span>
                    {step.skills && (
                      <p className="mt-0.5 text-xs text-mute">Skills: {step.skills.join(", ")}</p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}

      {careerInfo?.related_careers && careerInfo.related_careers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Related Careers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {careerInfo.related_careers.map((career) => (
                <Badge key={career} variant="outline">
                  {career}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-2 rounded-lg bg-canvas-soft px-4 py-3 text-xs text-mute">
        <Route className="h-4 w-4" />
        This intelligence is based only on evidence you&apos;ve demonstrated — assessments, projects, and resume matches.
      </div>
    </div>
  );
}
