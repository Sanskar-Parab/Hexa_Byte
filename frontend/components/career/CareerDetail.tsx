"use client";

import { CheckCircle2, XCircle, BookOpen, AlertTriangle, Zap, Target } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

  const getConfidenceColor = (confidence: string) => {
    switch (confidence?.toLowerCase()) {
      case "high": return "bg-emerald-100 text-emerald-700";
      case "medium": return "bg-amber-100 text-amber-700";
      default: return "bg-slate-100 text-slate-600";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "strong": return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "developing": return "bg-amber-50 text-amber-700 border-amber-200";
      case "gap": return "bg-rose-50 text-rose-700 border-rose-200";
      default: return "bg-slate-50 text-slate-700 border-slate-200";
    }
  };

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence?.toUpperCase()) {
      case "HIGH": return "bg-emerald-100 text-emerald-700";
      case "MEDIUM": return "bg-amber-100 text-amber-700";
      default: return "bg-slate-100 text-slate-600";
    }
  };

  const skillDetails = intelligence?.skill_details || [];
  const userCurrentSkills = intelligence?.user_current_skills || [];

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-2xl font-bold text-slate-900">{career.career_name}</h1>
          <Badge className={getConfidenceColor(career.confidence)}>
            {career.confidence} confidence
          </Badge>
        </div>
        {careerInfo?.description && (
          <p className="text-slate-600 leading-relaxed">{careerInfo.description}</p>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Match Score</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 text-white text-2xl font-bold">
              {scorePercent}%
            </div>
            <div className="flex-1">
              <div className="w-full bg-slate-100 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all"
                  style={{ width: `${scorePercent}%` }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {skillDetails.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Target className="h-5 w-5 text-blue-600" />
              Skill Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2 font-medium text-slate-600">Skill</th>
                    <th className="text-center py-2 font-medium text-slate-600">Your Level</th>
                    <th className="text-center py-2 font-medium text-slate-600">Importance</th>
                    <th className="text-center py-2 font-medium text-slate-600">Gap</th>
                    <th className="text-center py-2 font-medium text-slate-600">Confidence</th>
                    <th className="text-center py-2 font-medium text-slate-600">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {skillDetails.map((skill) => (
                    <tr key={skill.skill_name} className="border-b border-slate-100 last:border-0">
                      <td className="py-2.5 font-medium text-slate-900">{skill.skill_name}</td>
                      <td className="py-2.5 text-center text-slate-700">{skill.user_proficiency}/5</td>
                      <td className="py-2.5 text-center text-slate-700">{Math.round(skill.importance * 100)}%</td>
                      <td className="py-2.5 text-center text-slate-700">{skill.gap}</td>
                      <td className="py-2.5 text-center">
                        <Badge className={`text-xs ${getConfidenceBadge(skill.evidence_confidence)}`}>
                          {skill.evidence_confidence}
                        </Badge>
                      </td>
                      <td className="py-2.5 text-center">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(skill.status)}`}>
                          {skill.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {career.why_it_matches && career.why_it_matches.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Why This Matches You</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {career.why_it_matches.map((reason, i) => (
                <li key={i} className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500 mt-0.5 shrink-0" />
                  <span className="text-sm text-slate-700">{reason}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {career.strengths && career.strengths.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Your Strengths</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {career.strengths.map((s, i) => (
                <span key={i} className="text-sm bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full border border-emerald-200">
                  {s}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {career.skill_gaps && career.skill_gaps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Skills to Develop</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {career.skill_gaps.map((skill, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700">{skill}</span>
                  <XCircle className="h-4 w-4 text-amber-500" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {career.biggest_blocker && (
        <Card className="border-amber-200 bg-amber-50/50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              Biggest Blocker
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-700">
              <span className="font-semibold">{career.biggest_blocker}</span>
            </p>
            <p className="text-xs text-slate-500 mt-1">
              This is the highest-priority skill gap for this career. Focus on developing it first.
            </p>
          </CardContent>
        </Card>
      )}

      {career.recommended_action && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Zap className="h-5 w-5 text-blue-600" />
              Recommended Next Action
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-700">{career.recommended_action}</p>
          </CardContent>
        </Card>
      )}

      {userCurrentSkills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Your Current Skills</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {userCurrentSkills.map((skill, i) => (
                <span key={i} className="text-sm bg-slate-50 text-slate-700 px-3 py-1 rounded-full border border-slate-200">
                  {skill.name} ({skill.proficiency}/5)
                  <Badge className={`ml-1.5 text-xs ${getConfidenceBadge(skill.confidence)}`}>
                    {skill.confidence}
                  </Badge>
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {careerInfo?.required_skills && careerInfo.required_skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Required Skills</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {careerInfo.required_skills.map((skill) => (
                <Badge key={skill} variant="secondary" className="text-xs">
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
            <CardTitle className="text-lg flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-blue-600" />
              Learning Pathway
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-3">
              {careerInfo.learning_sequence.map((step: any, i: number) => (
                <li key={i} className="flex items-start gap-3">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-xs font-bold">
                    {i + 1}
                  </div>
                  <div>
                    <span className="text-sm font-medium text-slate-700">{step.title}</span>
                    {step.skills && (
                      <p className="text-xs text-slate-500 mt-0.5">
                        Skills: {step.skills.join(", ")}
                      </p>
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
            <CardTitle className="text-lg">Related Careers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {careerInfo.related_careers.map((career) => (
                <Badge key={career} variant="outline" className="text-xs">
                  {career}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
