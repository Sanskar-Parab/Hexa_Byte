"use client";

import { useState, useEffect } from "react";
import { ChatInterface } from "@/components/coach/ChatInterface";
import { api } from "@/lib/api";
import { CoachContext } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Bot,
  Target,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Lightbulb,
} from "lucide-react";

export default function CoachPage() {
  const [context, setContext] = useState<CoachContext | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadContext();
  }, []);

  const loadContext = async () => {
    try {
      const data = await api.getCoachContext();
      setContext(data);
    } catch {
      // Context loading failed — coach still works without it
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = async (question: string) => {
    const result = await api.askCoach(question);
    return {
      response: result.response,
      suggestions: result.suggestions || [],
    };
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Bot className="h-6 w-6 text-blue-600" />
          AI Career Coach
        </h1>
        <p className="text-slate-600 mt-1">
          Ask anything about your career path. Your coach uses your actual skill
          data, roadmap, and progress.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Context Panel */}
        <div className="lg:col-span-1 space-y-4">
          {!loading && context && (
            <>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-slate-600">
                    Your Context
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-500">Skills</span>
                    <Badge variant="secondary">{context.skills_count}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-500">Assessment</span>
                    {context.has_assessment ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-slate-300" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-500">Career Target</span>
                    {context.selected_career ? (
                      <Badge className="bg-blue-100 text-blue-700">
                        {context.selected_career}
                      </Badge>
                    ) : (
                      <span className="text-xs text-slate-400">None</span>
                    )}
                  </div>
                  {context.career_match_score !== null && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-500">Match Score</span>
                      <span className="text-sm font-medium">
                        {(context.career_match_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-500">Roadmap</span>
                    {context.has_roadmap ? (
                      <Badge className="bg-purple-100 text-purple-700">
                        {context.roadmap_progress} phases
                      </Badge>
                    ) : (
                      <span className="text-xs text-slate-400">None</span>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-500">Projects Done</span>
                    <Badge variant="secondary">{context.projects_completed}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-500">Evidence</span>
                    <Badge variant="secondary">{context.evidence_count}</Badge>
                  </div>
                </CardContent>
              </Card>

              {context.top_skill_gaps && context.top_skill_gaps.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-slate-600 flex items-center gap-1">
                      <Target className="h-4 w-4" />
                      Top Skill Gaps
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {context.top_skill_gaps.map((gap, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="text-slate-700">{gap.skill}</span>
                        <Badge variant="outline" className="text-xs">
                          gap: {gap.gap}
                        </Badge>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {context.next_best_action && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-slate-600 flex items-center gap-1">
                      <Lightbulb className="h-4 w-4" />
                      Next Best Action
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-700">
                      {context.next_best_action}
                    </p>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {loading && (
            <Card>
              <CardContent className="py-8 text-center text-sm text-slate-400">
                Loading context...
              </CardContent>
            </Card>
          )}
        </div>

        {/* Chat Interface */}
        <div className="lg:col-span-2">
          <div className="rounded-2xl border bg-white shadow-sm overflow-hidden">
            <ChatInterface onAsk={handleAsk} />
          </div>
        </div>
      </div>
    </div>
  );
}
