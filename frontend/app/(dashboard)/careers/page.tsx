"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Briefcase, Loader2 } from "lucide-react";
import { CareerCard } from "@/components/career/CareerCard";
import { api } from "@/lib/api";
import { CareerRecommendation } from "@/types";

export default function CareersPage() {
  const router = useRouter();
  const [careers, setCareers] = useState<CareerRecommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRecommendations()
      .then(setCareers)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Career Recommendations</h1>
        <p className="text-slate-600 mt-1">Based on your profile, here are your top career matches.</p>
      </div>

      {careers.length === 0 ? (
        <div className="text-center py-20">
          <Briefcase className="h-12 w-12 text-slate-300 mx-auto mb-3" />
          <h2 className="text-xl font-semibold text-slate-900">No Recommendations Yet</h2>
          <p className="text-slate-600 mt-2">Complete your profile and assessment to see career matches.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {careers.map((career) => (
            <CareerCard
              key={career.career_id}
              career={career}
              onSelect={(id) => {
                localStorage.setItem("selectedCareerId", id);
                router.push(`/careers/${id}`);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
