"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BarChart3, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SectionHeader } from "@/components/ui/section-header";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingState } from "@/components/ui/loading-state";
import { api } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function AssessmentResultPage() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAssessmentResult()
      .then(setResult)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <LoadingState message="Analyzing your responses..." />;
  }

  if (!result) {
    return (
      <div className="max-w-2xl mx-auto">
        <EmptyState
          icon={BarChart3}
          title="No results yet"
          description="Take the career fit assessment to see how your interests and strengths translate into results."
          actionLabel="Take Assessment"
          actionHref="/assessment"
        />
      </div>
    );
  }

  const chartData = Object.entries(result.scores || {}).map(([category, score]) => ({
    category: category.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
    score: Math.round((score as number) * 100),
  }));

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <SectionHeader
        eyebrow="Understand"
        title="Assessment Results"
        description="Here's what we learned about your career fit."
      />

      <Card>
        <CardHeader>
          <CardTitle>Your Assessment Scores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ebebeb" />
                <XAxis dataKey="category" tick={{ fontSize: 11, fill: "#4d4d4d" }} angle={-35} textAnchor="end" />
                <YAxis tick={{ fontSize: 12, fill: "#4d4d4d" }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    borderRadius: "8px",
                    border: "1px solid #ebebeb",
                  }}
                />
                <Bar dataKey="score" fill="#171717" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {result.interpretation && Object.keys(result.interpretation).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Interpretation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(result.interpretation).map(([key, value]) => (
                <div key={key} className="flex items-start gap-3">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-canvas-soft2 text-ink text-xs font-bold mt-0.5">
                    {key.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-ink">
                      {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                    </p>
                    <p className="text-sm text-body">{value as string}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {result.top_interests && result.top_interests.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Top Interests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {result.top_interests.map((interest: string, i: number) => (
                <span key={i} className="text-sm bg-link-soft text-link-deep px-3 py-1 rounded-full">
                  {interest}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col sm:flex-row gap-3">
        <Link href="/careers">
          <Button className="w-full sm:w-auto">
            View Career Recommendations
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </Link>
        <Link href="/dashboard">
          <Button variant="outline" className="w-full sm:w-auto">Back to Dashboard</Button>
        </Link>
      </div>
    </div>
  );
}
