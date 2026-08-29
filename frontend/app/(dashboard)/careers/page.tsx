"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Compass } from "lucide-react";
import { CareerCard } from "@/components/career/CareerCard";
import { SectionHeader } from "@/components/ui/section-header";
import { EmptyState } from "@/components/ui/empty-state";
import { CardSkeleton } from "@/components/ui/loading-state";
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

  return (
    <div className="max-w-6xl space-y-6">
      <SectionHeader
        eyebrow="Match"
        title="Careers That Fit You"
        description="Explore careers based on your demonstrated skills and interests."
      />

      {loading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : careers.length === 0 ? (
        <EmptyState
          icon={Compass}
          title="Your path starts here."
          description="Complete your profile and assessment so Next Path AI can find careers that match your demonstrated skills."
          actionLabel="Take the Assessment"
          actionHref="/assessment"
        />
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
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
