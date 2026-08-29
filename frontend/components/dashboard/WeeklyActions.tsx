"use client";

import { CheckSquare, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface WeeklyActionsProps {
  actions: string[];
}

export function WeeklyActions({ actions }: WeeklyActionsProps) {
  if (actions.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <CheckSquare className="mx-auto mb-3 h-10 w-10 text-hairline-strong" />
          <h3 className="mb-1 text-base font-semibold text-ink">All caught up</h3>
          <p className="text-sm text-body">No pending actions for this week.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
          <CheckSquare className="h-4 w-4 text-mute" />
          This Week&apos;s Actions
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-1">
          {actions.map((action, i) => (
            <li key={i} className="group flex items-center gap-3 rounded-lg px-2 py-2 -mx-2 transition-colors hover:bg-canvas-soft">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-hairline text-xs font-medium text-mute group-hover:border-ink group-hover:text-ink transition-colors">
                {i + 1}
              </div>
              <div className="flex flex-1 items-center justify-between">
                <span className="text-sm text-body group-hover:text-ink">{action}</span>
                <ArrowRight className="h-4 w-4 text-mute opacity-0 transition-opacity group-hover:opacity-100" />
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
