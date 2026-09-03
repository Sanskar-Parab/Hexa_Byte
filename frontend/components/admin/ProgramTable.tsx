"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronRight, GraduationCap } from "lucide-react";
import { formatPercent } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { ProgramAnalyticsRow } from "@/types";

export function ProgramTable({ programs }: { programs: ProgramAnalyticsRow[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold text-ink">Program Impact</CardTitle>
      </CardHeader>
      <CardContent>
        {programs.length === 0 ? (
          <EmptyState icon={GraduationCap} title="No programs yet" description="Training programs will appear here once trainees are enrolled." />
        ) : (
          <div className="space-y-2">
            {programs.map((p) => {
              const isOpen = expanded === p.training_program_id;
              return (
                <div key={p.training_program_id} className="rounded-lg border border-hairline">
                  <button
                    className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
                    onClick={() => setExpanded(isOpen ? null : p.training_program_id)}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {isOpen ? <ChevronDown className="h-4 w-4 shrink-0 text-mute" /> : <ChevronRight className="h-4 w-4 shrink-0 text-mute" />}
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-ink">{p.training_program_name}</p>
                        <p className="text-xs text-mute">{p.provider_name}{p.career_domain ? ` · ${p.career_domain}` : ""}</p>
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-4 text-xs text-body">
                      <span>{p.trainee_count} trainees</span>
                      {!p.sample_size_sufficient && <Badge variant="warning" className="text-[10px]">Small sample</Badge>}
                      <span className="hidden sm:inline">Placement: {formatPercent(p.placement_rate)}</span>
                    </div>
                  </button>

                  {isOpen && (
                    <div className="border-t border-hairline px-4 py-3">
                      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                        <Stat label="Completion" value={formatPercent(p.training_completion_rate)} />
                        <Stat label="Placement" value={formatPercent(p.placement_rate)} />
                        <Stat label="Employment" value={formatPercent(p.employment_rate)} />
                        <Stat label="6-mo Retention" value={formatPercent(p.retention_6_month_rate)} />
                        <Stat label="Training Relevance" value={formatPercent(p.training_relevant_employment_rate)} />
                        <Stat label="Unemployment" value={formatPercent(p.unemployment_rate)} />
                      </div>

                      {p.skill_gaps.length > 0 && (
                        <div className="mt-4">
                          <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-mute">Skill gaps</p>
                          <div className="flex flex-wrap gap-1.5">
                            {p.skill_gaps.map((g) => (
                              <Badge key={g.skill} variant="outline">{g.skill} · {formatPercent(g.percentage)}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-mute">{label}</p>
      <p className={cn("text-sm font-medium", value === "No data" ? "text-mute" : "text-ink")}>{value}</p>
    </div>
  );
}
