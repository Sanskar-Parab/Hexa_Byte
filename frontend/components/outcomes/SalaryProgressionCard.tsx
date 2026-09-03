"use client";

import { Wallet, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { formatCurrency, formatDate, cn } from "@/lib/utils";
import type { SalaryProgression } from "@/types";

const POINTS: { key: keyof Omit<SalaryProgression, "changes">; label: string }[] = [
  { key: "initial", label: "Starting" },
  { key: "at_3_months", label: "3 Months" },
  { key: "at_6_months", label: "6 Months" },
  { key: "at_12_months", label: "12 Months" },
];

export function SalaryProgressionCard({ progression }: { progression: SalaryProgression }) {
  const knownPoints = POINTS.filter((p) => progression[p.key]);

  if (knownPoints.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
            <Wallet className="h-4 w-4 text-mute" />
            Salary Progression
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Wallet}
            title="No salary data shared yet"
            description="Salary is never required — this fills in as check-ins report it."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
          <Wallet className="h-4 w-4 text-mute" />
          Salary Progression
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-4">
          {POINTS.map((p) => {
            const snapshot = progression[p.key];
            return (
              <div
                key={p.key}
                className={cn(
                  "rounded-lg border border-hairline p-3",
                  snapshot ? "bg-canvas" : "bg-canvas-soft2 opacity-60"
                )}
              >
                <p className="text-xs font-medium uppercase tracking-wide text-mute">{p.label}</p>
                <p className="mt-1.5 text-base font-semibold text-ink">
                  {snapshot ? formatCurrency(snapshot.amount, snapshot.currency) : "—"}
                </p>
                {snapshot && <p className="mt-0.5 text-[11px] text-mute">as of {formatDate(snapshot.date)}</p>}
              </div>
            );
          })}
        </div>

        {progression.changes.length > 0 && (
          <div className="mt-4 space-y-2 border-t border-hairline pt-4">
            {progression.changes.map((change, i) => {
              const positive = change.absolute_change >= 0;
              const Icon = positive ? ArrowUpRight : ArrowDownRight;
              return (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-body">
                    {formatDate(change.from_date)} → {formatDate(change.to_date)}
                  </span>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1 font-medium",
                      positive ? "text-link-deep" : "text-err-deep"
                    )}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {positive ? "+" : ""}
                    {formatCurrency(change.absolute_change, progression.initial?.currency)}
                    {change.percentage_change !== null && (
                      <span className="text-xs text-mute">
                        ({positive ? "+" : ""}
                        {change.percentage_change}%)
                      </span>
                    )}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
