"use client";

import { Check, X, Clock, HelpCircle, GraduationCap, Briefcase, Rocket } from "lucide-react";
import { cn, formatDate, formatCurrency } from "@/lib/utils";
import { RelevanceBadge } from "./RelevanceBadge";
import type { OutcomeTimeline, RetentionStatus } from "@/types";

type DotState = "done" | "failed" | "pending" | "unknown" | "not_started";

function TimelineDot({ state, icon: Icon }: { state: DotState; icon?: React.ElementType }) {
  if (state === "done") {
    return (
      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-ink text-white shadow-card">
        {Icon ? <Icon className="h-4 w-4" /> : <Check className="h-4 w-4" />}
      </div>
    );
  }
  if (state === "failed") {
    return (
      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-err text-white shadow-card">
        <X className="h-4 w-4" />
      </div>
    );
  }
  if (state === "unknown") {
    return (
      <div className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-warn bg-warn-soft text-warn-deep">
        <HelpCircle className="h-4 w-4" />
      </div>
    );
  }
  if (state === "pending") {
    return (
      <div className="relative flex h-9 w-9 items-center justify-center">
        <span className="absolute inline-flex h-full w-full animate-pulse rounded-full bg-warn/30" />
        <div className="relative flex h-7 w-7 items-center justify-center rounded-full border-2 border-warn bg-warn-soft">
          <Clock className="h-3.5 w-3.5 text-warn-deep" />
        </div>
      </div>
    );
  }
  return <div className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-dashed border-hairline-strong bg-canvas" />;
}

const RETENTION_LABEL: Record<RetentionStatus, string> = {
  yes: "Retained",
  no: "Not retained",
  pending: "Milestone not yet reached",
  unknown: "No check-in recorded yet",
  not_applicable: "Not applicable",
};

interface NodeDef {
  key: string;
  title: string;
  state: DotState;
  dateLabel?: string | null;
  body?: React.ReactNode;
}

export function OutcomeMilestoneTimeline({ timeline }: { timeline: OutcomeTimeline }) {
  const { training, placement, employment, milestones, retention, training_relevance_over_time } = timeline;

  const relevanceFor = (months: number) =>
    training_relevance_over_time.find((r) => r.months_since_employment === months);

  const nodes: NodeDef[] = [
    {
      key: "training",
      title: "Training",
      state: !training ? "not_started" : training.enrollment_status === "completed" ? "done" : "pending",
      dateLabel: training?.completion_date ? `Completed ${formatDate(training.completion_date)}` : training?.enrollment_status.replace("_", " "),
      body: training ? (
        <p className="text-sm text-body">{training.training_program_name}</p>
      ) : (
        <p className="text-sm text-mute">No training enrollment on record.</p>
      ),
    },
    {
      key: "placement",
      title: "Placement",
      state: placement ? "done" : "not_started",
      dateLabel: placement ? placement.employment_status.replace("_", " ") : undefined,
      body: placement ? (
        <div className="space-y-1">
          {placement.source_opportunity_title && (
            <p className="text-sm text-body">Recommended opportunity: {placement.source_opportunity_title}</p>
          )}
          <p className="text-xs text-mute">{placement.verified ? "Verified" : "Self-reported"}</p>
        </div>
      ) : (
        <p className="text-sm text-mute">Not placed yet.</p>
      ),
    },
    {
      key: "employment",
      title: "Job Started",
      state: employment?.employment_start_date ? "done" : "not_started",
      dateLabel: employment?.employment_start_date ? formatDate(employment.employment_start_date) : undefined,
      body: employment?.employment_start_date ? (
        <div className="space-y-1.5">
          <p className="text-sm text-body">
            {employment.job_title || "Role"} {employment.company_name ? `at ${employment.company_name}` : ""}
          </p>
          {relevanceFor(0) && <RelevanceBadge level={relevanceFor(0)!.level} />}
        </div>
      ) : (
        <p className="text-sm text-mute">No employment start date on record.</p>
      ),
    },
    ...([3, 6, 12] as const).map((months): NodeDef => {
      const milestone = milestones[`${months}_month` as "3_month" | "6_month" | "12_month"];
      const status = retention[`${months}_month` as "3_month" | "6_month" | "12_month"];
      const state: DotState =
        status === "yes" ? "done" : status === "no" ? "failed" : status === "pending" ? "pending" : status === "unknown" ? "unknown" : "not_started";
      const salaryKey = (`at_${months}_months` as const);
      const salary = timeline.salary_progression[salaryKey];
      const relevance = relevanceFor(months);

      return {
        key: `${months}_month`,
        title: `${months} Months`,
        state,
        dateLabel: milestone ? formatDate(milestone.milestone_date) : undefined,
        body: milestone ? (
          <div className="space-y-1.5">
            <p className="text-sm text-body">{RETENTION_LABEL[status]}</p>
            {milestone.employment_status && (
              <p className="text-xs capitalize text-mute">Status: {milestone.employment_status.replace("_", " ")}</p>
            )}
            {salary && <p className="text-xs text-mute">Salary: {formatCurrency(salary.amount, salary.currency)}</p>}
            {relevance && <RelevanceBadge level={relevance.level} />}
          </div>
        ) : (
          <p className="text-sm text-mute">Not applicable — no employment start date recorded.</p>
        ),
      };
    }),
  ];

  return (
    <div className="relative">
      <div className="absolute left-[18px] top-2 bottom-2 w-px bg-hairline" />
      <div className="space-y-6">
        {nodes.map((node, i) => (
          <div key={node.key} className={cn("relative flex gap-5", node.state === "not_started" && "opacity-70")}>
            <div className="relative z-10 shrink-0 pt-0.5">
              <TimelineDot state={node.state} icon={i === 0 ? GraduationCap : i === 1 ? Briefcase : i === 2 ? Rocket : undefined} />
            </div>
            <div className="min-w-0 flex-1 rounded-xl border border-hairline bg-canvas p-4 pb-4 shadow-card">
              <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
                <span className="font-mono text-xs uppercase tracking-wide text-mute">{node.title}</span>
                {node.dateLabel && <span className="text-xs capitalize text-mute">{node.dateLabel}</span>}
              </div>
              {node.body}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
