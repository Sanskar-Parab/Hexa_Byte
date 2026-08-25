"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <ClipboardCheck className="h-6 w-6 text-blue-600" />
          Job Reality Check
        </h1>
        <p className="text-slate-600 mt-1">
          Paste a job description to see how your skills match up.
        </p>
      </div>

      {!matchResult && (
        <JobAnalyzer onAnalysisComplete={setMatchResult} />
      )}

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

      {history.length > 0 && !matchResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <History className="h-5 w-5 text-slate-500" />
              Previous Analyses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <ClipboardCheck className="h-5 w-5 text-slate-400" />
                    <div>
                      <p className="font-medium text-sm text-slate-800">{item.job_title}</p>
                      <p className="text-xs text-slate-500">
                        {item.required_skills.length} required skills
                        {item.match_result && (
                          <> · {item.match_result.alignment_percentage}% match</>
                        )}
                        {" · "}
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(item.id)}
                    className="text-slate-400 hover:text-rose-600"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {loading && (
        <div className="text-center text-slate-500 py-8">Loading...</div>
      )}
    </div>
  );
}
