"use client";

import { GraduationCap, Briefcase, Building2, Wallet } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { OutcomeTimeline } from "@/types";

function StatCard({
  icon: Icon,
  label,
  value,
  meta,
}: {
  icon: React.ElementType;
  label: string;
  value: React.ReactNode;
  meta?: React.ReactNode;
}) {
  return (
    <Card>
      <CardContent className="p-4 sm:p-5">
        <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-mute">
          <Icon className="h-3.5 w-3.5" />
          {label}
        </div>
        <div className="text-lg font-semibold tracking-tight text-ink">{value}</div>
        {meta && <div className="mt-1 text-xs text-body">{meta}</div>}
      </CardContent>
    </Card>
  );
}

export function OutcomeSummaryCards({ timeline }: { timeline: OutcomeTimeline }) {
  const { training, placement, employment, salary_progression } = timeline;

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        icon={GraduationCap}
        label="Training Completed"
        value={training ? training.training_program_name || "Training Program" : "Not started"}
        meta={
          training?.completion_date
            ? `Completed ${formatDate(training.completion_date)}`
            : training
              ? `Status: ${training.enrollment_status.replace("_", " ")}`
              : "No training on record yet"
        }
      />

      <StatCard
        icon={Briefcase}
        label="Placement"
        value={
          placement ? (
            <span className="capitalize">{placement.employment_status.replace("_", " ")}</span>
          ) : (
            "Not placed yet"
          )
        }
        meta={
          placement?.source_opportunity_title
            ? `Via recommendation: ${placement.source_opportunity_title}`
            : placement
              ? placement.verified ? "Verified" : "Self-reported"
              : undefined
        }
      />

      <StatCard
        icon={Building2}
        label="Current Employment"
        value={employment?.job_title || (employment ? "Role not specified" : "—")}
        meta={
          employment?.company_name
            ? `${employment.company_name}${employment.employment_end_date ? " · Ended" : ""}`
            : undefined
        }
      />

      <StatCard
        icon={Wallet}
        label="Salary"
        value={
          salary_progression.initial
            ? formatCurrency(salary_progression.initial.amount, salary_progression.initial.currency)
            : "Not shared"
        }
        meta={
          salary_progression.changes.length > 0 ? (
            <Badge
              variant={salary_progression.changes[salary_progression.changes.length - 1].absolute_change >= 0 ? "success" : "destructive"}
              className="text-[10px]"
            >
              {salary_progression.changes[salary_progression.changes.length - 1].absolute_change >= 0 ? "+" : ""}
              {salary_progression.changes[salary_progression.changes.length - 1].percentage_change ?? "—"}% since start
            </Badge>
          ) : (
            salary_progression.initial?.period
          )
        }
      />
    </div>
  );
}
