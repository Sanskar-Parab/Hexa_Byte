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
    <div className="rounded-xl border border-hairline bg-canvas p-6 shadow-card">
      <Badge variant="secondary" className="text-xs mb-4">{formatCategory(question.category)}</Badge>
      <h3 className="text-lg font-semibold text-ink mb-6">{question.question_text}</h3>
      <div className="space-y-3">
        {question.options.map((option, index) => (
          <button
            key={index}
            onClick={() => onSelect(question.id, index)}
            className={cn(
              "w-full text-left rounded-lg border p-4 transition-all duration-150",
              selectedAnswer === index
                ? "border-ink bg-canvas-soft2 shadow-card"
                : "border-hairline hover:border-hairline-strong hover:bg-canvas-soft"
            )}
          >
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-sm font-medium",
                  selectedAnswer === index
                    ? "border-ink bg-ink text-white"
                    : "border-hairline-strong text-mute"
                )}
              >
                {String.fromCharCode(65 + index)}
              </div>
              <span className={cn(
                "text-sm",
                selectedAnswer === index ? "text-ink font-medium" : "text-body"
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
