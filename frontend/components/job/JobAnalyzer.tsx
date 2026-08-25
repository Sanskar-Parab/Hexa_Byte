"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Search, ClipboardCheck } from "lucide-react";
import { api } from "@/lib/api";

interface JobAnalyzerProps {
  onAnalysisComplete: (result: any) => void;
}

export function JobAnalyzer({ onAnalysisComplete }: JobAnalyzerProps) {
  const [description, setDescription] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!description.trim()) return;
    setAnalyzing(true);
    setError(null);
    try {
      const result = await api.analyzeJob(description);
      onAnalysisComplete(result);
    } catch (err: any) {
      setError(err.message || "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ClipboardCheck className="h-5 w-5 text-blue-600" />
          Job Description Analyzer
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-slate-600">
          Paste a job description below. We&apos;ll extract requirements and match them against your skills.
        </p>

        <Textarea
          placeholder="Paste the full job description here...

Example:
Software Engineer - React/Node.js

Requirements:
- 3+ years of experience with JavaScript
- Proficiency in React and Node.js
- Experience with PostgreSQL
- Familiarity with AWS or GCP
- Strong communication skills

Nice to have:
- TypeScript experience
- Docker and Kubernetes
- CI/CD pipeline experience"
          value={description}
          onChange={(e) => { setDescription(e.target.value); setError(null); }}
          rows={12}
          className="font-mono text-sm"
        />

        {error && (
          <p className="text-sm text-rose-600 bg-rose-50 rounded-lg px-4 py-2">{error}</p>
        )}

        <Button
          onClick={handleAnalyze}
          disabled={!description.trim() || analyzing}
          className="w-full"
        >
          {analyzing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Search className="mr-2 h-4 w-4" />
              Analyze Job Match
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
