"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BarChart3, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="text-center py-20">
        <BarChart3 className="h-12 w-12 text-slate-300 mx-auto mb-3" />
        <h2 className="text-xl font-semibold text-slate-900">No Results Yet</h2>
        <p className="text-slate-600 mt-2">Take the assessment to see your results.</p>
        <Link href="/assessment">
          <Button className="mt-4">Take Assessment</Button>
        </Link>
      </div>
    );
  }

  const chartData = Object.entries(result.scores || {}).map(([category, score]) => ({
    category: category.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
    score: Math.round((score as number) * 100),
  }));

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Assessment Results</h1>
        <p className="text-slate-600 mt-1">Here&apos;s what we learned about your career fit.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your Assessment Scores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="category" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" />
                <YAxis tick={{ fontSize: 12 }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    borderRadius: "8px",
                    border: "1px solid #e2e8f0",
                  }}
                />
                <Bar dataKey="score" fill="#3b82f6" radius={[6, 6, 0, 0]} />
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
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-xs font-bold mt-0.5">
                    {key.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                    </p>
                    <p className="text-sm text-slate-600">{value as string}</p>
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
                <span key={i} className="text-sm bg-blue-50 text-blue-700 px-3 py-1 rounded-full border border-blue-200">
                  {interest}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-3">
        <Link href="/careers">
          <Button>
            View Career Recommendations
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </Link>
        <Link href="/dashboard">
          <Button variant="outline">Back to Dashboard</Button>
        </Link>
      </div>
    </div>
  );
}
