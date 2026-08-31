"use client";

import { useState, useEffect } from "react";
import { ChatInterface } from "@/components/coach/ChatInterface";
import { api } from "@/lib/api";
import { CoachContext } from "@/types";
import { SectionHeader } from "@/components/ui/section-header";
import { SkeletonBlock } from "@/components/ui/loading-state";
import { Target, Gauge, Flame, Map } from "lucide-react";
import { cn } from "@/lib/utils";

function ContextTile({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Target;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-hairline bg-canvas p-4 shadow-card">
      <div className="mb-2 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-mute">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="truncate text-sm font-semibold text-ink" title={value}>
        {value}
      </p>
    </div>
  );
}

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

  const handleAsk = async (
    question: string,
    conversation: { role: "user" | "assistant"; content: string }[]
  ) => {
    const result = await api.askCoach(question, conversation);
    return {
      response: result.response,
      suggestions: result.suggestions || [],
    };
  };

  const topGap = context?.top_skill_gaps?.[0]?.skill ?? null;

  const tiles = [
    context?.selected_career
      ? { icon: Target, label: "Target Career", value: context.selected_career }
      : null,
    context?.career_match_score != null
      ? { icon: Gauge, label: "Readiness", value: `${Math.round(context.career_match_score * 100)}%` }
      : null,
    topGap ? { icon: Flame, label: "Current Gap", value: topGap } : null,
    context?.roadmap_progress
      ? { icon: Map, label: "Current Phase", value: context.roadmap_progress }
      : null,
  ].filter(Boolean) as { icon: typeof Target; label: string; value: string }[];

  return (
    <div className="mx-auto max-w-4xl">
      <SectionHeader
        eyebrow="AI Coach"
        title="Your AI Career Coach"
        description="Personalized guidance based on your actual career progress."
        className="mb-6"
      />

      {loading && (
        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-xl border border-hairline bg-canvas p-4 shadow-card">
              <SkeletonBlock className="h-3 w-16" />
              <SkeletonBlock className="mt-3 h-4 w-full" />
            </div>
          ))}
        </div>
      )}

      {!loading && tiles.length > 0 && (
        <div className={cn("mb-6 grid gap-3", tiles.length === 1 ? "grid-cols-1" : tiles.length === 2 ? "grid-cols-2" : tiles.length === 3 ? "grid-cols-3" : "grid-cols-2 sm:grid-cols-4")}>
          {tiles.map((tile) => (
            <ContextTile key={tile.label} {...tile} />
          ))}
        </div>
      )}

      {!loading && tiles.length === 0 && (
        <div className="mb-6 rounded-xl border border-dashed border-hairline bg-canvas-soft p-4 text-sm text-body">
          Pick a target career and complete an assessment to get coaching grounded in your real progress — you can still ask questions in the meantime.
        </div>
      )}

      <ChatInterface onAsk={handleAsk} focusSkill={topGap} />
    </div>
  );
}
