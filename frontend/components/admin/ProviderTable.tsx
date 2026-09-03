"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Badge } from "@/components/ui/badge";
import { Building2 } from "lucide-react";
import { formatPercent, formatCurrency } from "@/lib/utils";
import type { ProviderComparisonRow } from "@/types";

export function ProviderTable({ providers }: { providers: ProviderComparisonRow[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold text-ink">Provider Performance</CardTitle>
      </CardHeader>
      <CardContent>
        {providers.length === 0 ? (
          <EmptyState icon={Building2} title="No providers yet" description="Training programs will appear here once trainees are enrolled." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="border-b border-hairline text-left text-xs font-medium uppercase tracking-wide text-mute">
                  <th className="py-2 pr-4">Provider</th>
                  <th className="py-2 pr-4">Trainees</th>
                  <th className="py-2 pr-4">Completion</th>
                  <th className="py-2 pr-4">Placement</th>
                  <th className="py-2 pr-4">Employment</th>
                  <th className="py-2 pr-4">6-mo Retention</th>
                  <th className="py-2 pr-4">Avg. Salary</th>
                  <th className="py-2 pr-4">Training Relevance</th>
                </tr>
              </thead>
              <tbody>
                {providers.map((p) => (
                  <tr key={p.provider_name} className="border-b border-hairline last:border-0">
                    <td className="py-3 pr-4 font-medium text-ink">{p.provider_name}</td>
                    <td className="py-3 pr-4 text-body">
                      {p.trainee_count}
                      {!p.sample_size_sufficient && (
                        <Badge variant="warning" className="ml-2 text-[10px]">Small sample</Badge>
                      )}
                    </td>
                    <td className="py-3 pr-4 text-body">{formatPercent(p.training_completion_rate)}</td>
                    <td className="py-3 pr-4 text-body">{formatPercent(p.placement_rate)}</td>
                    <td className="py-3 pr-4 text-body">{formatPercent(p.employment_rate)}</td>
                    <td className="py-3 pr-4 text-body">{formatPercent(p.retention_6_month_rate)}</td>
                    <td className="py-3 pr-4 text-body">
                      {p.average_current_salary === null ? "No data" : formatCurrency(p.average_current_salary)}
                    </td>
                    <td className="py-3 pr-4 text-body">{formatPercent(p.training_relevant_employment_rate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="mt-3 text-xs text-mute">
          Providers with fewer than 5 trainees show trainee count only — rates are suppressed rather than shown as an unreliable ranking.
        </p>
      </CardContent>
    </Card>
  );
}
