"use client";

import { CheckCircle2, XCircle, BookOpen } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface CareerDetailProps {
  career: {
    career_id: string;
    career_name: string;
    match_score: number;
    confidence: string;
    why_it_matches: string[];
    strengths: string[];
    skill_gaps: string[];
  };
  careerInfo?: {
    description?: string;
    required_skills?: string[];
    learning_sequence?: any[];
    related_careers?: string[];
  };
}

export function CareerDetail({ career, careerInfo }: CareerDetailProps) {
  const scorePercent = Math.round(career.match_score * 100);

  const getConfidenceColor = (confidence: string) => {
    switch (confidence?.toLowerCase()) {
      case "high": return "bg-emerald-100 text-emerald-700";
      case "medium": return "bg-amber-100 text-amber-700";
      default: return "bg-slate-100 text-slate-600";
    }
  };

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
