"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AssessmentQuestion } from "@/components/assessment/AssessmentQuestion";
import { AssessmentProgress } from "@/components/assessment/AssessmentProgress";
import { SectionHeader } from "@/components/ui/section-header";
import { LoadingState } from "@/components/ui/loading-state";
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
  const allAnswered = questions.length > 0 && answeredCount === questions.length;

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
    return <LoadingState message="Preparing your assessment..." />;
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <SectionHeader
        eyebrow="Understand"
        title="Career Fit Assessment"
        description="Answer these questions to help us understand your strengths, interests, and work preferences."
      />

      <div className="sticky top-16 z-10 -mx-4 bg-canvas-soft/95 backdrop-blur px-4 py-3 sm:mx-0 sm:rounded-xl sm:border sm:border-hairline sm:bg-canvas sm:px-4 sm:shadow-card">
        <AssessmentProgress current={answeredCount} total={questions.length} />
      </div>

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
        <CardContent className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-sm text-body">
            {answeredCount} of {questions.length} questions answered
          </p>
          <Button onClick={handleSubmit} disabled={!allAnswered || submitting} className="w-full sm:w-auto">
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Submit Assessment
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
