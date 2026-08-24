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
          <CheckSquare className="h-12 w-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-900 mb-1">All Caught Up</h3>
          <p className="text-sm text-slate-500">No pending actions for this week.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <CheckSquare className="h-5 w-5 text-emerald-500" />
          This Week&apos;s Actions
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {actions.map((action, i) => (
            <li key={i} className="flex items-start gap-3 group">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 border-slate-200 group-hover:border-blue-400 transition-colors mt-0.5">
                <span className="text-xs font-medium text-slate-400 group-hover:text-blue-500">{i + 1}</span>
              </div>
              <div className="flex-1 flex items-center justify-between">
                <span className="text-sm text-slate-700">{action}</span>
                <ArrowRight className="h-4 w-4 text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
