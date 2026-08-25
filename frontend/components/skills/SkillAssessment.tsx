"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
        return "bg-green-100 text-green-700";
      case "intermediate":
        return "bg-blue-100 text-blue-700";
      case "advanced":
        return "bg-purple-100 text-purple-700";
      case "practical":
        return "bg-amber-100 text-amber-700";
      default:
        return "bg-slate-100 text-slate-700";
    }
  };

  const proficiencyColor = (p: number) => {
    if (p <= 2) return "text-orange-600";
    if (p <= 3) return "text-blue-600";
    return "text-green-600";
  };

  if (phase === "idle") {
    // Show checking AI status
    if (checkingAI) {
      return (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Brain className="h-5 w-5 text-blue-600" />
              AI Skill Assessment
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
              <p className="text-sm text-slate-600">Checking AI availability...</p>
            </div>
          </CardContent>
        </Card>
      );
    }

    // Show AI status warning banner if AI is not available, but allow starting standard assessment
    const isAiAvailable = aiStatus?.available ?? false;

    return (
      <Card className={`border-blue-200 ${isAiAvailable ? "bg-blue-50/50" : "bg-amber-50/50 border-amber-200"}`}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-600" />
            {isAiAvailable ? "AI Skill Assessment" : "Skill Assessment (Standard Mode)"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isAiAvailable && (
            <div className="bg-amber-100 border border-amber-200 rounded-lg p-3 space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-800">
                <WifiOff className="h-4 w-4 text-amber-600" />
                <span>AI Service Notice: {aiStatus?.error || "AI service unavailable"}</span>
              </div>
              <p className="text-xs text-amber-700">
                Standard Assessment Mode is active with verified static questions. Configure <strong>GROQ_API_KEY</strong> for dynamic AI question generation.
              </p>
            </div>
          )}

          <p className="text-sm text-slate-600">
            Take a 10-question assessment to determine your actual{" "}
            <strong>{skillName}</strong> proficiency level.
          </p>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              3 Beginner
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-blue-500" />
              3 Intermediate
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-purple-500" />
              2 Advanced
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              2 Practical
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleStart} className="bg-blue-600 hover:bg-blue-700">
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
      <Card className="border-red-200 bg-red-50/50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2 text-red-700">
            <AlertCircle className="h-5 w-5" />
            Assessment Error
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-red-600">{error}</p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onCancel}>
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to Skills
            </Button>
            <Button onClick={handleStart} className="bg-blue-600 hover:bg-blue-700">
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (phase === "submitting") {
    return (
      <Card>
        <CardContent className="py-12 text-center space-y-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto" />
          <p className="text-sm text-slate-600">Evaluating your answers...</p>
        </CardContent>
      </Card>
    );
  }

  if (phase === "result" && result) {
    return (
      <Card className="border-green-200">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            Assessment Complete
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center">
            <h3 className="text-xl font-bold text-slate-900">{result.skill.name}</h3>
            <div className="mt-2">
              <span className={`text-4xl font-bold ${proficiencyColor(result.proficiency)}`}>
                {result.proficiency}/5
              </span>
              <p className="text-sm text-slate-500 mt-1">{result.level_name}</p>
            </div>
            <p className="text-sm text-slate-600 mt-1">
              Score: {result.score_percentage}%
            </p>
            <div className="flex items-center justify-center gap-1 mt-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
                result.confidence === "HIGH"
                  ? "text-emerald-700 bg-emerald-50 border-emerald-200"
                  : result.confidence === "MEDIUM"
                  ? "text-amber-700 bg-amber-50 border-amber-200"
                  : "text-rose-700 bg-rose-50 border-rose-200"
              }`}>
                Confidence: {result.confidence}
              </span>
            </div>
          </div>

          {result.strengths.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Strengths
              </h4>
              <ul className="space-y-1">
                {result.strengths.map((s, i) => (
                  <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">•</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.weaknesses.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1">
                <AlertCircle className="h-4 w-4 text-amber-500" />
                Areas to Improve
              </h4>
              <ul className="space-y-1">
                {result.weaknesses.map((w, i) => (
                  <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                    <span className="text-amber-500 mt-0.5">•</span>
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.recommended_topics.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1">
                <BookOpen className="h-4 w-4 text-blue-500" />
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
            <p className="text-sm text-slate-600 italic">{result.summary}</p>
          )}

          <div className="flex gap-2">
            <Button onClick={handleSave} className="bg-blue-600 hover:bg-blue-700">
              Save Skill Level
            </Button>
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
          <div className="w-full bg-slate-200 rounded-full h-2 mt-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${((currentIndex + 1) / total) * 100}%` }}
            />
          </div>
          <p className="text-xs text-slate-500">
            Question {currentIndex + 1} of {total}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Badge className={difficultyColor(question.difficulty)}>
              {question.difficulty}
            </Badge>
          </div>

          <div className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">
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
                      ? "border-blue-500 bg-blue-50 text-blue-900"
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
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
              <Button
                onClick={handleSubmit}
                disabled={!allAnswered}
                className="bg-green-600 hover:bg-green-700"
              >
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
