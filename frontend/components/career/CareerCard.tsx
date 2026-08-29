"use client";

import { ArrowRight, Circle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConfidenceBadge } from "@/components/ui/status-badge";
import { Card } from "@/components/ui/card";

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

  return (
    <Card className="group flex flex-col p-6 transition-all duration-200 hover:shadow-card-hover hover:-translate-y-0.5">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <h3 className="text-lg font-semibold text-ink group-hover:text-link transition-colors">
            {career.career_name}
          </h3>
          <ConfidenceBadge confidence={career.confidence} className="mt-2" />
        </div>
        <div className="flex h-14 w-14 shrink-0 flex-col items-center justify-center rounded-xl bg-ink text-white">
          <span className="text-base font-bold leading-none">{scorePercent}%</span>
          <span className="mt-1 text-[9px] font-medium uppercase tracking-wide text-white/60">match</span>
        </div>
      </div>

      {career.strengths && career.strengths.length > 0 && (
        <div className="mb-3">
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-mute">Why it fits</p>
          <ul className="space-y-1">
            {career.strengths.slice(0, 3).map((s, i) => (
              <li key={i} className="flex items-center gap-1.5 text-sm text-body">
                <span className="text-link">✓</span> {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {career.skill_gaps && career.skill_gaps.length > 0 && (
        <div className="mb-4">
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-mute">Skill gaps</p>
          <ul className="space-y-1">
            {career.skill_gaps.slice(0, 2).map((s, i) => (
              <li key={i} className="flex items-center gap-1.5 text-sm text-body">
                <Circle className="h-2.5 w-2.5 shrink-0 fill-hairline-strong text-hairline-strong" /> {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {career.recommended_action && (
        <div className="mb-4 rounded-lg bg-canvas-soft px-3 py-2.5">
          <p className="text-xs font-semibold uppercase tracking-wide text-mute mb-0.5">Next action</p>
          <p className="text-sm text-ink line-clamp-2">{career.recommended_action}</p>
        </div>
      )}

      <Button
        variant="ghost"
        className="mt-auto w-full justify-between group/btn"
        onClick={() => onSelect(career.career_id)}
      >
        View Career
        <ArrowRight className="h-4 w-4 transition-transform group-hover/btn:translate-x-1" />
      </Button>
    </Card>
  );
}
