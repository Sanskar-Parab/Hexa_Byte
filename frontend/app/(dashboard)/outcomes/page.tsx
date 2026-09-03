"use client";

import { useCallback, useEffect, useState } from "react";
import { Award } from "lucide-react";
import { SectionHeader } from "@/components/ui/section-header";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { OutcomeSummaryCards } from "@/components/outcomes/OutcomeSummaryCards";
import { OutcomeMilestoneTimeline } from "@/components/outcomes/OutcomeMilestoneTimeline";
import { SalaryProgressionCard } from "@/components/outcomes/SalaryProgressionCard";
import { CheckInHistory } from "@/components/outcomes/CheckInHistory";
import { ReportOutcomeForm } from "@/components/outcomes/ReportOutcomeForm";
import { api } from "@/lib/api";
import type { OutcomeTimeline } from "@/types";

export default function OutcomesPage() {
  const [timeline, setTimeline] = useState<OutcomeTimeline | null>(null);
  const [loading, setLoading] = useState(true);

  const loadTimeline = useCallback(() => {
    return api
      .getOutcomeTimeline()
      .then(setTimeline)
      .catch(() => setTimeline(null));
  }, []);

  useEffect(() => {
    loadTimeline().finally(() => setLoading(false));
  }, [loadTimeline]);

  if (loading) {
    return <LoadingState message="Loading your career outcomes..." />;
  }

  const hasOutcomeData = timeline && (timeline.training || timeline.placement);

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <SectionHeader
        eyebrow="Career Outcomes"
        title="Your Employment Journey"
        description="From training to placement to where you are now — tracked over time, with nothing assumed or filled in for you."
      />

      <ReportOutcomeForm onUpdated={loadTimeline} />

      {!hasOutcomeData && (
        <EmptyState
          icon={Award}
          title="Your career outcomes will show up here."
          description="Once you enroll in a training program and report a placement above, we'll track your employment journey — retention, salary progression, and how relevant your job stays to your training — right here."
        />
      )}

      {hasOutcomeData && timeline && (
        <>
          <OutcomeSummaryCards timeline={timeline} />

          <div>
            <h3 className="mb-4 text-base font-semibold tracking-tight text-ink">Timeline</h3>
            <OutcomeMilestoneTimeline timeline={timeline} />
          </div>

          <SalaryProgressionCard progression={timeline.salary_progression} />

          <CheckInHistory checkIns={timeline.check_ins} />
        </>
      )}
    </div>
  );
}
