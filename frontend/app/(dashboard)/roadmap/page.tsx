"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Map } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingState } from "@/components/ui/loading-state";
import { RoadmapTimeline } from "@/components/roadmap/RoadmapTimeline";
import { api } from "@/lib/api";
import { Roadmap } from "@/types";

export default function RoadmapPage() {
  const router = useRouter();
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCareerId, setSelectedCareerId] = useState<string | null>(null);

  useEffect(() => {
    const careerId = localStorage.getItem("selectedCareerId");
    setSelectedCareerId(careerId);

    api.getRoadmap(careerId || undefined)
      .then(setRoadmap)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleUpdateStatus = async (phaseId: string, status: string) => {
    try {
      await api.updatePhaseStatus(phaseId, status);
      setRoadmap((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          phases: prev.phases.map((p) =>
            p.id === phaseId ? { ...p, status: status as any } : p
          ),
        };
      });
    } catch (err) {
      console.error("Failed to update phase status:", err);
    }
  };

  if (loading) {
    return <LoadingState message="Building your personalized path..." />;
  }

  if (!roadmap) {
    return (
      <div className="mx-auto max-w-2xl py-10">
        <EmptyState
          icon={Map}
          title="Your path starts here."
          description={
            selectedCareerId
              ? "Generate your personalized learning roadmap from your selected career."
              : "Choose a career and we'll build a roadmap around your current skills and gaps."
          }
          actionLabel={selectedCareerId ? "Go to Career Details" : "Explore Careers"}
          actionHref={selectedCareerId ? `/careers/${selectedCareerId}` : "/careers"}
        />
      </div>
    );
  }

  const includedPhases = roadmap.phases.filter((p) => p.adaptation_mode !== "skipped");
  const completedPhases = includedPhases.filter((p) => p.status === "completed").length;
  const skippedCount = roadmap.phases.filter((p) => p.adaptation_mode === "skipped").length;
  const progress = includedPhases.length > 0
    ? Math.round((completedPhases / includedPhases.length) * 100)
    : 0;

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <p className="mb-2 font-mono text-xs uppercase tracking-wider text-mute">Roadmap</p>
        <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
          Your Path to {roadmap.career_name}
        </h1>
        {roadmap.summary && (
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-body">{roadmap.summary}</p>
        )}
      </div>

      <div className="flex items-center justify-between rounded-xl border border-hairline bg-canvas p-5 shadow-card">
        <div>
          <p className="text-sm text-body">Phases complete</p>
          <p className="mt-1 text-lg font-semibold text-ink">
            {completedPhases}/{includedPhases.length}
            {skippedCount > 0 && (
              <span className="ml-2 text-sm font-normal text-mute">({skippedCount} skipped)</span>
            )}
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-semibold tracking-tight text-ink">{progress}%</p>
          <p className="text-xs text-mute">Ready</p>
        </div>
      </div>

      <RoadmapTimeline phases={roadmap.phases} onUpdateStatus={handleUpdateStatus} />
    </div>
  );
}
