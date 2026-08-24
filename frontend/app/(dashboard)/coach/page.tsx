"use client";

import { ChatInterface } from "@/components/coach/ChatInterface";
import { api } from "@/lib/api";

export default function CoachPage() {
  const handleAsk = async (question: string) => {
    const result = await api.askCoach(question);
    return {
      response: result.response,
      suggestions: [],
    };
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">AI Career Coach</h1>
        <p className="text-slate-600 mt-1">Ask anything about your career journey.</p>
      </div>

      <div className="rounded-2xl border bg-white shadow-sm overflow-hidden">
        <ChatInterface onAsk={handleAsk} />
      </div>
    </div>
  );
}
