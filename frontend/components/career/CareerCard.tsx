"use client";

import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";

interface CareerCardProps {
  career: {
    career_id: string;
    career_name: string;
    match_score: number;
    confidence: string;
    why_it_matches?: string[];
    strengths?: string[];
    skill_gaps?: string[];
    biggest_blocker?: string | null;
    recommended_action?: string | null;
  };
  onSelect: (id: string) => void;
}

export function CareerCard({ career, onSelect }: CareerCardProps) {
  const scorePercent = Math.round(career.match_score * 100);

  const getConfidenceColor = (confidence: string) => {
    switch (confidence?.toLowerCase()) {
      case "high": return "bg-emerald-100 text-emerald-700";
      case "medium": return "bg-amber-100 text-amber-700";
      default: return "bg-slate-100 text-slate-600";
    }
  };

  return (
    <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5 overflow-hidden">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 group-hover:text-blue-700 transition-colors">
              {career.career_name}
            </h3>
            <Badge className={`mt-1.5 text-xs ${getConfidenceColor(career.confidence)}`}>
              {career.confidence} confidence
            </Badge>
          </div>
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 text-white text-lg font-bold shadow-lg shadow-blue-500/25">
            {scorePercent}%
          </div>
        </div>

        {career.why_it_matches && career.why_it_matches.length > 0 && (
          <p className="text-sm text-slate-600 leading-relaxed mb-4 line-clamp-2">
            {career.why_it_matches[0]}
          </p>
        )}

        <div className="mb-4">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
            <span>Match Score</span>
            <span className="font-medium text-slate-700">{scorePercent}%</span>
          </div>
          <Progress
            value={scorePercent}
            className="h-2"
          />
        </div>

        {career.strengths && career.strengths.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-slate-500 mb-1.5">Your Strengths</p>
            <div className="flex flex-wrap gap-1">
              {career.strengths.slice(0, 3).map((s, i) => (
                <span key={i} className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        <Button
          variant="ghost"
          className="w-full justify-between group/btn"
          onClick={() => onSelect(career.career_id)}
        >
          View Details
          <ArrowRight className="h-4 w-4 transition-transform group-hover/btn:translate-x-1" />
        </Button>
      </CardContent>
    </Card>
  );
}
