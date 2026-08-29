"use client";

import { Check } from "lucide-react";
import { ConfidenceBadge } from "@/components/ui/status-badge";
import { SkillBar } from "@/components/ui/skill-bar";
import { SkillDetail } from "@/types";

interface SkillGapChartProps {
  skillDetails: SkillDetail[];
}

export function SkillGapChart({ skillDetails }: SkillGapChartProps) {
  return (
    <div>
      {/* Desktop table */}
      <div className="hidden overflow-x-auto sm:block">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left">
              <th className="py-2 pr-3 font-medium text-mute">Skill</th>
              <th className="py-2 px-3 font-medium text-mute">Required</th>
              <th className="py-2 px-3 font-medium text-mute">Your Level</th>
              <th className="py-2 pl-3 text-right font-medium text-mute">Gap</th>
            </tr>
          </thead>
          <tbody>
            {skillDetails.map((skill) => {
              const required = Math.max(1, Math.round(skill.importance * 5));
              return (
                <tr key={skill.skill_name} className="border-b border-hairline last:border-0">
                  <td className="py-3 pr-3">
                    <p className="font-medium text-ink">{skill.skill_name}</p>
                    <ConfidenceBadge confidence={skill.evidence_confidence} className="mt-1" />
                  </td>
                  <td className="py-3 px-3 text-body">{required}/5</td>
                  <td className="py-3 px-3">
                    <div className="w-28">
                      <SkillBar proficiency={skill.user_proficiency} />
                    </div>
                  </td>
                  <td className="py-3 pl-3 text-right">
                    {skill.gap > 0 ? (
                      <span className="font-medium text-warn-deep">{skill.gap}</span>
                    ) : (
                      <Check className="ml-auto h-4 w-4 text-link" />
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile stacked cards */}
      <div className="space-y-3 sm:hidden">
        {skillDetails.map((skill) => {
          const required = Math.max(1, Math.round(skill.importance * 5));
          return (
            <div key={skill.skill_name} className="rounded-lg border border-hairline p-3">
              <div className="mb-2 flex items-center justify-between">
                <p className="font-medium text-ink">{skill.skill_name}</p>
                {skill.gap > 0 ? (
                  <span className="text-xs font-medium text-warn-deep">Gap: {skill.gap}</span>
                ) : (
                  <Check className="h-4 w-4 text-link" />
                )}
              </div>
              <SkillBar proficiency={skill.user_proficiency} showLevelLabel />
              <div className="mt-2 flex items-center justify-between text-xs text-mute">
                <span>Required: {required}/5</span>
                <ConfidenceBadge confidence={skill.evidence_confidence} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
