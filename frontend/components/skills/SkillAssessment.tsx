"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingState } from "@/components/ui/loading-state";
import { api } from "@/lib/api";
import {
  Brain,
  ChevronRight,
  ChevronLeft,
  CheckCircle2,
  AlertCircle,
  BookOpen,
  ArrowLeft,
  ShieldCheck,
  WifiOff,
} from "lucide-react";

interface AssessmentQuestion {
  id: number;
  difficulty: string;
  type: string;
  question: string;
  options: string[];
}

interface AssessmentStartResponse {
  assessment_id: string;
  skill: { id: string; name: string };
  questions: AssessmentQuestion[];
}

interface AssessmentResult {
  assessment_id: string;
  skill: { id: string; name: string };
  proficiency: number;
  level_name: string;
  score_percentage: number;
  strengths: string[];
  weaknesses: string[];
  recommended_topics: string[];
  summary: string;
  confidence: string;
}

interface SkillAssessmentProps {
  skillId: string;
  skillName: string;
  onComplete: () => void;
  onCancel: () => void;
}

type Phase = "idle" | "taking" | "submitting" | "result" | "error";

export function SkillAssessment({
  skillId,
  skillName,
  onComplete,
  onCancel,
}: SkillAssessmentProps) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [assessment, setAssessment] = useState<AssessmentStartResponse | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aiStatus, setAiStatus] = useState<{ available: boolean; error: string | null } | null>(null);
  const [checkingAI, setCheckingAI] = useState(true);

  useEffect(() => {
    checkAIAvailability();
  }, []);

  const checkAIAvailability = async () => {
    try {
      setCheckingAI(true);
      const status = await api.checkAIStatus();
      setAiStatus(status);
    } catch (err: any) {
      setAiStatus({ available: false, error: "Failed to check AI status" });
    } finally {
      setCheckingAI(false);
    }
  };

  const handleStart = async () => {
    setError(null);
    try {
      const response = await api.startSkillAssessment(skillId);
      setAssessment(response);
      setPhase("taking");
    } catch (err: any) {
      setError(err.message || "Failed to start assessment");
      setPhase("error");
    }
  };

  const handleAnswer = (questionId: number, answer: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }));
  };

  const handleNext = () => {
    if (!assessment) return;
    if (currentIndex < assessment.questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    if (!assessment) return;
    setPhase("submitting");
    try {
      const answerList = Object.entries(answers).map(([qid, answer]) => ({
        question_id: parseInt(qid),
        answer,
      }));
      const response = await api.submitSkillAssessment(assessment.assessment_id, answerList);
      setResult(response);
      setPhase("result");
    } catch (err: any) {
      setError(err.message || "Failed to submit assessment");
      setPhase("error");
    }
  };

  const handleSave = () => {
    onComplete();
  };

  const difficultyColor = (d: string) => {
    switch (d) {
      case "beginner":
        return "bg-link-soft text-link-deep";
      case "intermediate":
        return "bg-warn-soft text-warn-deep";
      case "advanced":
        return "bg-violet-soft text-violet-deep";
      case "practical":
        return "bg-canvas-soft2 text-body";
      default:
        return "bg-canvas-soft2 text-body";
    }
  };

  const proficiencyColor = (p: number) => {
    if (p <= 2) return "text-warn-deep";
    if (p <= 3) return "text-link-deep";
    return "text-link";
  };

  const confidenceStyle = (confidence: string) =>
    confidence === "HIGH"
      ? "text-link-deep bg-link-soft border-link-soft"
      : confidence === "MEDIUM"
      ? "text-warn-deep bg-warn-soft border-warn-soft"
      : "text-err-deep bg-err-soft border-err-soft";

  if (phase === "idle") {
    if (checkingAI) {
      return (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Brain className="h-5 w-5 text-ink" />
              AI Skill Assessment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <LoadingState message="Checking AI availability..." className="py-6" />
          </CardContent>
        </Card>
      );
    }

    const isAiAvailable = aiStatus?.available ?? false;

    return (
      <Card className={!isAiAvailable ? "border-warn-soft bg-warn-soft/20" : undefined}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Brain className="h-5 w-5 text-ink" />
            {isAiAvailable ? "AI Skill Assessment" : "Skill Assessment (Standard Mode)"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isAiAvailable && (
            <div className="bg-warn-soft border border-warn-soft rounded-lg p-3 space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-warn-deep">
                <WifiOff className="h-4 w-4" />
                <span>AI Service Notice: {aiStatus?.error || "AI service unavailable"}</span>
              </div>
              <p className="text-xs text-warn-deep">
                Standard Assessment Mode is active with verified static questions. Configure <strong>GROQ_API_KEY</strong> for dynamic AI question generation.
              </p>
            </div>
          )}

          <p className="text-sm text-body">
            Take a 10-question assessment to determine your actual{" "}
            <strong className="text-ink">{skillName}</strong> proficiency level.
          </p>
          <div className="flex flex-wrap items-center gap-3 text-xs text-mute">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-link" />
              3 Beginner
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-warn" />
              3 Intermediate
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-violet" />
              2 Advanced
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-mute" />
              2 Practical
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleStart}>
              {isAiAvailable ? "Start AI Assessment" : "Start Standard Assessment"}
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
            {!isAiAvailable && (
              <Button onClick={checkAIAvailability} variant="outline">
                Check AI Again
              </Button>
            )}
            <Button variant="outline" onClick={onCancel}>
              Set Level Manually
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (phase === "error") {
    return (
      <Card className="border-err-soft bg-err-soft/20">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2 text-err-deep">
            <AlertCircle className="h-5 w-5" />
            Assessment Error
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-err-deep">{error}</p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onCancel}>
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to Skills
            </Button>
            <Button onClick={handleStart}>Try Again</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (phase === "submitting") {
    return (
      <Card>
        <CardContent>
          <LoadingState message="Evaluating your answers..." className="py-10" />
        </CardContent>
      </Card>
    );
  }

  if (phase === "result" && result) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-link" />
            Assessment Complete
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center">
            <h3 className="text-xl font-semibold text-ink">{result.skill.name}</h3>
            <div className="mt-2">
              <span className={`text-4xl font-bold ${proficiencyColor(result.proficiency)}`}>
                {result.proficiency}/5
              </span>
              <p className="text-sm text-mute mt-1">{result.level_name}</p>
            </div>
            <p className="text-sm text-body mt-1">
              Score: {result.score_percentage}%
            </p>
            <div className="flex items-center justify-center gap-1 mt-2">
              <ShieldCheck className="h-4 w-4 text-link" />
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${confidenceStyle(result.confidence)}`}>
                Confidence: {result.confidence}
              </span>
            </div>
          </div>

          {result.strengths.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-ink mb-2 flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4 text-link" />
                Strengths
              </h4>
              <ul className="space-y-1">
                {result.strengths.map((s, i) => (
                  <li key={i} className="text-sm text-body flex items-start gap-2">
                    <span className="text-link mt-0.5">•</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.weaknesses.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-ink mb-2 flex items-center gap-1">
                <AlertCircle className="h-4 w-4 text-warn-deep" />
                Areas to Improve
              </h4>
              <ul className="space-y-1">
                {result.weaknesses.map((w, i) => (
                  <li key={i} className="text-sm text-body flex items-start gap-2">
                    <span className="text-warn-deep mt-0.5">•</span>
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.recommended_topics.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-ink mb-2 flex items-center gap-1">
                <BookOpen className="h-4 w-4 text-link" />
                Recommended Topics
              </h4>
              <div className="flex flex-wrap gap-2">
                {result.recommended_topics.map((t, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {t}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {result.summary && (
            <p className="text-sm text-body italic">{result.summary}</p>
          )}

          <div className="flex gap-2">
            <Button onClick={handleSave}>Save Skill Level</Button>
            <Button variant="outline" onClick={onCancel}>
              Discard
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (phase === "taking" && assessment) {
    const question = assessment.questions[currentIndex];
    const answered = Object.keys(answers).length;
    const total = assessment.questions.length;
    const isLast = currentIndex === total - 1;
    const allAnswered = answered === total;

    return (
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{skillName} Assessment</CardTitle>
            <Badge variant="outline">{answered}/{total} answered</Badge>
          </div>
          <div className="w-full bg-hairline rounded-full h-1.5 mt-2">
            <div
              className="bg-ink h-1.5 rounded-full transition-all"
              style={{ width: `${((currentIndex + 1) / total) * 100}%` }}
            />
          </div>
          <p className="text-xs text-mute">
            Question {currentIndex + 1} of {total}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Badge className={difficultyColor(question.difficulty)}>
              {question.difficulty}
            </Badge>
          </div>

          <div className="text-sm text-ink whitespace-pre-wrap leading-relaxed">
            {question.question}
          </div>

          <div className="space-y-2">
            {question.options.map((option, idx) => {
              const letter = String.fromCharCode(65 + idx);
              const isSelected = answers[question.id] === letter;
              return (
                <button
                  key={idx}
                  onClick={() => handleAnswer(question.id, letter)}
                  className={`w-full text-left p-3 rounded-lg border text-sm transition-colors ${
                    isSelected
                      ? "border-ink bg-canvas-soft2 text-ink"
                      : "border-hairline hover:border-hairline-strong hover:bg-canvas-soft"
                  }`}
                >
                  <span className="font-medium mr-2">{letter}.</span>
                  {option}
                </button>
              );
            })}
          </div>

          <div className="flex items-center justify-between pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrev}
              disabled={currentIndex === 0}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>

            {isLast ? (
              <Button onClick={handleSubmit} disabled={!allAnswered}>
                Submit Assessment
              </Button>
            ) : (
              <Button onClick={handleNext} disabled={!answers[question.id]}>
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
}
