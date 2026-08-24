"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface AssessmentQuestionProps {
  question: {
    id: string;
    question_text: string;
    category: string;
    options: string[];
  };
  selectedAnswer: number | null;
  onSelect: (questionId: string, answerIndex: number) => void;
}

export function AssessmentQuestion({ question, selectedAnswer, onSelect }: AssessmentQuestionProps) {
  const formatCategory = (cat: string) => {
    return cat.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <Badge variant="secondary" className="text-xs mb-2">{formatCategory(question.category)}</Badge>
      </div>
      <h3 className="text-lg font-semibold text-slate-900 mb-6">{question.question_text}</h3>
      <div className="space-y-3">
        {question.options.map((option, index) => (
          <button
            key={index}
            onClick={() => onSelect(question.id, index)}
            className={cn(
              "w-full text-left rounded-xl border-2 p-4 transition-all duration-200",
              selectedAnswer === index
                ? "border-blue-500 bg-blue-50 shadow-sm"
                : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
            )}
          >
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 text-sm font-medium",
                  selectedAnswer === index
                    ? "border-blue-500 bg-blue-500 text-white"
                    : "border-slate-300 text-slate-500"
                )}
              >
                {String.fromCharCode(65 + index)}
              </div>
              <span className={cn(
                "text-sm",
                selectedAnswer === index ? "text-blue-700 font-medium" : "text-slate-700"
              )}>
                {option}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
