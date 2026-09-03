"use client";

import { useState } from "react";
import { FlaskConical, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DemoDatasetBannerProps {
  demoTraineeCount: number;
  totalTraineeCount: number;
  onLoadDemoData: () => Promise<void>;
}

export function DemoDatasetBanner({ demoTraineeCount, totalTraineeCount, onLoadDemoData }: DemoDatasetBannerProps) {
  const [loading, setLoading] = useState(false);

  const handleLoad = async () => {
    setLoading(true);
    try {
      await onLoadDemoData();
    } finally {
      setLoading(false);
    }
  };

  if (totalTraineeCount === 0) {
    return (
      <div className="flex flex-col items-start gap-3 rounded-xl border border-violet/30 bg-violet-soft/30 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <FlaskConical className="mt-0.5 h-4 w-4 shrink-0 text-violet-deep" />
          <p className="text-sm text-violet-deep">
            No outcome data yet. Load a clearly-labelled synthetic demo dataset to explore the dashboard —
            it is never real Maharashtra Government data.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleLoad} disabled={loading} className="shrink-0">
          {loading ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <FlaskConical className="mr-1.5 h-3.5 w-3.5" />}
          Load Demo Dataset
        </Button>
      </div>
    );
  }

  if (demoTraineeCount === 0) {
    return null;
  }

  const allDemo = demoTraineeCount === totalTraineeCount;

  return (
    <div className="flex items-start gap-3 rounded-xl border border-violet/30 bg-violet-soft/30 p-4">
      <FlaskConical className="mt-0.5 h-4 w-4 shrink-0 text-violet-deep" />
      <p className="text-sm text-violet-deep">
        <span className="font-semibold">Demo Dataset: </span>
        {allDemo
          ? `All ${totalTraineeCount} trainees in this view are synthetic demo data.`
          : `${demoTraineeCount} of ${totalTraineeCount} trainees in this view are synthetic demo data.`}
        {" "}This is for demonstration only and does not represent real Maharashtra Government data.
      </p>
    </div>
  );
}
