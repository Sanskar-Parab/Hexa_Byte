"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AssessmentQuestion } from "@/components/assessment/AssessmentQuestion";
import { AssessmentProgress } from "@/components/assessment/AssessmentProgress";
import { api } from "@/lib/api";
import { AssessmentQuestion as QuestionType } from "@/types";

export default function AssessmentPage() {
  const router = useRouter();
  const [questions, setQuestions] = useState<QuestionType[]>([]);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.getAssessmentQuestions()
      .then(setQuestions)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = (questionId: string, answerIndex: number) => {
    setAnswers({ ...answers, [questionId]: answerIndex });
  };

  const answeredCount = Object.keys(answers).length;
  const allAnswered = answeredCount === questions.length;

  const handleSubmit = async () => {
    if (!allAnswered) return;
    setSubmitting(true);
    try {
      await api.submitAssessment(answers);
      router.push("/assessment/result");
    } catch {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Career Fit Assessment</h1>
        <p className="text-slate-600 mt-1">
          Answer these questions to help our system understand your strengths and preferences.
        </p>
      </div>

      <AssessmentProgress current={answeredCount} total={questions.length} />

      <div className="space-y-4">
        {questions.map((q) => (
          <AssessmentQuestion
            key={q.id}
            question={q}
            selectedAnswer={answers[q.id] ?? null}
            onSelect={handleSelect}
          />
        ))}
      </div>

      <Card>
        <CardContent className="p-6 flex items-center justify-between">
          <p className="text-sm text-slate-600">
            {answeredCount} of {questions.length} questions answered
          </p>
          <Button onClick={handleSubmit} disabled={!allAnswered || submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Submit Assessment
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
