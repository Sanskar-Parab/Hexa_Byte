"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FolderKanban, Route } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { api } from "@/lib/api";
import { RecommendedProject } from "@/types";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<RecommendedProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCareerId, setSelectedCareerId] = useState<string | null>(null);

  useEffect(() => {
    const careerId = localStorage.getItem("selectedCareerId");
    setSelectedCareerId(careerId);

    if (careerId) {
      api.getProjectRecommendations(careerId)
        .then(setProjects)
        .catch(() => {})
        .finally(() => setLoading(false));
    } else {
      api.getStoredRecommendations()
        .then((recs) => {
          if (recs.length > 0) {
            const topCareerId = recs[0].career_id;
            localStorage.setItem("selectedCareerId", topCareerId);
            setSelectedCareerId(topCareerId);
            return api.getProjectRecommendations(topCareerId);
          }
          return [];
        })
        .then(setProjects)
        .catch(() => {})
        .finally(() => setLoading(false));
    }
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
        <h1 className="text-2xl font-bold text-slate-900">Recommended Projects</h1>
        <p className="text-slate-600 mt-1">Build your portfolio with projects matched to your goals.</p>
      </div>

      {projects.length === 0 ? (
        <div className="text-center py-20">
          <FolderKanban className="h-12 w-12 text-slate-300 mx-auto mb-3" />
          <h2 className="text-xl font-semibold text-slate-900">No Projects Yet</h2>
          <p className="text-slate-600 mt-2">
            {selectedCareerId
              ? "Generate your roadmap to receive project recommendations."
              : "Select a career and generate a roadmap to see recommended projects."}
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
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  );
}
