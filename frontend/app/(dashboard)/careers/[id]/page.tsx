"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Route } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CareerDetail } from "@/components/career/CareerDetail";
import { api } from "@/lib/api";

export default function CareerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const careerId = params.id as string;
  const [recommendation, setRecommendation] = useState<any>(null);
  const [careerInfo, setCareerInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!careerId) {
      setLoading(false);
      return;
    }

    localStorage.setItem("selectedCareerId", careerId);

    Promise.all([
      api.getStoredRecommendations().catch(() => []),
      api.getCareerDetail(careerId).catch(() => null),
    ])
      .then(([recs, info]) => {
        const found = recs.find((r: any) => String(r.career_id) === String(careerId));
        setRecommendation(found || null);
        setCareerInfo(info);
      })
      .catch(() => {
        setError("Unable to load career details. Please try again.");
      })
      .finally(() => setLoading(false));
  }, [careerId]);

  const handleGenerateRoadmap = async () => {
    setGenerating(true);
    try {
      await api.generateRoadmap(careerId);
      router.push("/roadmap");
    } catch {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold text-slate-900">Unable to load career details</h2>
        <p className="text-slate-600 mt-2">{error}</p>
        <Button variant="ghost" onClick={() => router.push("/careers")} className="mt-4">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Careers
        </Button>
      </div>
    );
  }

  if (!careerInfo && !recommendation) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold text-slate-900">Career not found</h2>
        <p className="text-slate-600 mt-2">This career may no longer exist.</p>
        <Button variant="ghost" onClick={() => router.push("/careers")} className="mt-4">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Careers
        </Button>
      </div>
    );
  }

  const displayName = recommendation?.career_name || careerInfo?.name || "Career";
  const displayRecommendation = recommendation || {
    career_id: careerId,
    career_name: displayName,
    match_score: 0,
    confidence: "",
    why_it_matches: [],
    strengths: [],
    skill_gaps: [],
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Button variant="ghost" onClick={() => router.push("/careers")} className="mb-2">
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Careers
      </Button>

      <CareerDetail career={displayRecommendation} careerInfo={careerInfo} />

      <div className="flex gap-3">
        <Button onClick={handleGenerateRoadmap} disabled={generating}>
          {generating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          <Route className="mr-2 h-4 w-4" />
          Build My Personalized Roadmap
        </Button>
      </div>
    </div>
  );
}
