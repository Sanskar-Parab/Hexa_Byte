"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Map, Route } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!roadmap) {
    return (
      <div className="text-center py-20">
        <Map className="h-12 w-12 text-slate-300 mx-auto mb-3" />
        <h2 className="text-xl font-semibold text-slate-900">No Roadmap Yet</h2>
        <p className="text-slate-600 mt-2">
          {selectedCareerId
            ? "Generate your personalized learning roadmap from your selected career."
            : "Select a career to generate your personalized learning roadmap."}
        </p>
        {selectedCareerId ? (
          <Button onClick={() => router.push(`/careers/${selectedCareerId}`)} className="mt-4">
            <Route className="mr-2 h-4 w-4" /> Go to Career Details
          </Button>
        ) : (
          <Button onClick={() => router.push("/careers")} className="mt-4">
            Browse Careers
          </Button>
        )}
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
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Learning Roadmap</h1>
        <p className="text-slate-600 mt-1">
          Your personalized path to <span className="font-medium text-blue-600">{roadmap.career_name}</span>
        </p>
        {roadmap.summary && (
          <p className="text-sm text-slate-500 mt-1">{roadmap.summary}</p>
        )}
      </div>

      <Card>
        <CardContent className="p-4 flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-600">Progress</p>
            <p className="text-lg font-bold text-slate-900">
              {completedPhases}/{includedPhases.length} phases
              {skippedCount > 0 && (
                <span className="text-sm font-normal text-slate-500 ml-2">
                  ({skippedCount} skipped)
                </span>
              )}
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-blue-600">{progress}%</p>
          </div>
        </CardContent>
      </Card>

      <RoadmapTimeline phases={roadmap.phases} onUpdateStatus={handleUpdateStatus} />
    </div>
  );
}
