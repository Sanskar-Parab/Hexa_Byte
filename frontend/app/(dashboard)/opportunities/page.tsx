"use client";

import { useCallback, useEffect, useState } from "react";
import { Briefcase, AlertCircle } from "lucide-react";
import { SectionHeader } from "@/components/ui/section-header";
import { LoadingState, CardSkeleton } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { OpportunityCard } from "@/components/opportunities/OpportunityCard";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { OpportunityRecommendation } from "@/types";

type TypeFilter = "all" | "internship" | "job";

const MIN_MATCH_OPTIONS = [
  { value: "0", label: "Any match" },
  { value: "40", label: "40%+ match" },
  { value: "60", label: "60%+ match" },
  { value: "80", label: "80%+ match" },
];

export default function OpportunitiesPage() {
  const [type, setType] = useState<TypeFilter>("all");
  const [minMatch, setMinMatch] = useState("0");
  const [recommendations, setRecommendations] = useState<OpportunityRecommendation[]>([]);
  const [skillCount, setSkillCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<"ok" | "unavailable">("ok");
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const careerId = typeof window !== "undefined" ? localStorage.getItem("selectedCareerId") : null;
      const data = await api.getOpportunityRecommendations({
        type,
        limit: 20,
        minMatch: Number(minMatch),
        careerId: careerId || undefined,
      });
      setRecommendations(data.recommendations);
      setSkillCount(data.user_skill_summary.skill_count);
      setStatus(data.source_status);
      setMessage(data.message);
    } catch (err) {
      setRecommendations([]);
      setStatus("unavailable");
      setMessage("Job and internship data is temporarily unavailable. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [type, minMatch]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <SectionHeader
        eyebrow="Opportunities in India"
        title="Jobs & Internships"
        description="Real openings from across the web, ranked by how well they match your demonstrated skills — not just keywords."
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-1 rounded-lg border border-hairline bg-canvas-soft p-1">
          {(["all", "internship", "job"] as TypeFilter[]).map((t) => (
            <button
              key={t}
              onClick={() => setType(t)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium capitalize transition-colors",
                type === t ? "bg-canvas text-ink shadow-card" : "text-body hover:text-ink"
              )}
            >
              {t === "all" ? "All" : `${t}s`}
            </button>
          ))}
        </div>

        <Select value={minMatch} onValueChange={setMinMatch}>
          <SelectTrigger className="w-full sm:w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {MIN_MATCH_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {skillCount === 0 && !loading && (
        <div className="flex items-start gap-3 rounded-xl border border-warn/20 bg-warn-soft/40 p-4">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-warn-deep" />
          <p className="text-sm text-warn-deep">
            Add skills to your profile to get personalized matches — right now these are unranked results.
          </p>
        </div>
      )}

      {loading && (
        <div className="space-y-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      )}

      {!loading && status === "unavailable" && (
        <EmptyState
          icon={AlertCircle}
          title="Opportunity data is temporarily unavailable"
          description={message || "Please try again in a few minutes."}
          actionLabel="Try Again"
          onAction={load}
        />
      )}

      {!loading && status === "ok" && recommendations.length === 0 && (
        <EmptyState
          icon={Briefcase}
          title="No opportunities found"
          description={message || "Try lowering the minimum match or switching the type filter."}
        />
      )}

      {!loading && status === "ok" && recommendations.length > 0 && (
        <div className="space-y-4">
          {recommendations.map((opp) => (
            <OpportunityCard key={`${opp.type}-${opp.id}`} opportunity={opp} />
          ))}
        </div>
      )}
    </div>
  );
}
