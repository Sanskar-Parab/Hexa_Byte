"use client";

import { Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { formatDate, formatCurrency } from "@/lib/utils";
import type { OutcomeCheckInSummary } from "@/types";

export function CheckInHistory({ checkIns }: { checkIns: OutcomeCheckInSummary[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
          <Clock className="h-4 w-4 text-mute" />
          Check-in History
        </CardTitle>
      </CardHeader>
      <CardContent>
        {checkIns.length === 0 ? (
          <EmptyState
            icon={Clock}
            title="No check-ins yet"
            description="Periodic check-ins (3, 6, and 12 months after starting) build your retention and salary history over time."
          />
        ) : (
          <div className="space-y-3">
            {checkIns.map((c) => (
              <div key={c.id} className="rounded-lg border border-hairline p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-medium text-ink">{formatDate(c.check_in_date)}</span>
                  <Badge variant="secondary" className="capitalize">{c.employment_status.replace("_", " ")}</Badge>
                </div>
                <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-body">
                  {c.job_title && <span>{c.job_title}{c.company_name ? ` at ${c.company_name}` : ""}</span>}
                  {c.salary !== null && <span>{formatCurrency(c.salary, c.salary_currency)}</span>}
                  {c.months_since_employment !== null && <span>{c.months_since_employment} months in</span>}
                </div>
                {c.reason_for_leaving && (
                  <p className="mt-1.5 text-xs text-mute">Reason for leaving: {c.reason_for_leaving}</p>
                )}
                {c.notes && <p className="mt-1.5 text-xs text-mute">{c.notes}</p>}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
