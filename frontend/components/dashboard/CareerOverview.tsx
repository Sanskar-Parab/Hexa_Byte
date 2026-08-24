"use client";

import Link from "next/link";
import { Briefcase, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";

interface CareerOverviewProps {
  targetCareer: string | null;
  matchScore: number;
  readiness: number;
}

export function CareerOverview({ targetCareer, matchScore, readiness }: CareerOverviewProps) {
  if (!targetCareer) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <Briefcase className="h-12 w-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-900 mb-1">No Career Target Set</h3>
          <p className="text-sm text-slate-500 mb-4">Choose a career to get started.</p>
          <Link href="/careers">
            <Button size="sm">Browse Careers</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Briefcase className="h-5 w-5 text-blue-600" />
          Target Career
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h3 className="text-xl font-bold text-slate-900">{targetCareer}</h3>
          <Badge variant="success" className="mt-1">
            <TrendingUp className="mr-1 h-3 w-3" />
            {matchScore}% Match
          </Badge>
        </div>

        <div>
          <div className="flex items-center justify-between text-sm mb-1.5">
            <span className="text-slate-600">Career Readiness</span>
            <span className="font-semibold text-slate-900">{readiness}%</span>
          </div>
          <Progress value={readiness} className="h-2.5" />
        </div>

        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs text-slate-500">
            Keep working on your roadmap to increase your career readiness score.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
