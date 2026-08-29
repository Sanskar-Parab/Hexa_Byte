"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SectionHeader } from "@/components/ui/section-header";
import { LoadingState } from "@/components/ui/loading-state";
import { ClipboardCheck, History, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { JobAnalyzer } from "@/components/job/JobAnalyzer";
import { JobMatchResults } from "@/components/job/JobMatchResults";
import type { JobMatchResult, JobAnalysisDetail } from "@/types";

export default function JobAnalyzerPage() {
  const [matchResult, setMatchResult] = useState<JobMatchResult | null>(null);
  const [history, setHistory] = useState<JobAnalysisDetail[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await api.getJobHistory();
      setHistory(data);
    } catch (err) {
      console.error("Failed to load job history", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteJobAnalysis(id);
      setHistory(history.filter((h) => h.id !== id));
    } catch (err) {
      console.error("Failed to delete job analysis", err);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <SectionHeader
        eyebrow="Job Match"
        title="Job Reality Check"
        description="Paste a real job description to see how your demonstrated skills actually line up."
      />

      {!matchResult && <JobAnalyzer onAnalysisComplete={setMatchResult} />}

      {matchResult && (
        <div className="space-y-4">
          <JobMatchResults result={matchResult} />
          <Button
            variant="outline"
            onClick={() => {
              setMatchResult(null);
              loadHistory();
            }}
          >
            Analyze Another Job
          </Button>
        </div>
      )}

      {loading && <LoadingState message="Loading your job analyses..." />}

      {!loading && history.length > 0 && !matchResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <History className="h-4 w-4 text-mute" />
              Previous Analyses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-lg border border-hairline bg-canvas-soft p-3 transition-colors hover:bg-canvas-soft2"
                >
                  <div className="flex items-center gap-3">
                    <ClipboardCheck className="h-5 w-5 text-mute" />
                    <div>
                      <p className="text-sm font-medium text-ink">{item.job_title}</p>
                      <p className="text-xs text-mute">
                        {item.required_skills.length} required skills
                        {item.match_result && <> · {item.match_result.alignment_percentage}% match</>}
                        {" · "}
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(item.id)}
                    className="text-mute hover:text-err"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
