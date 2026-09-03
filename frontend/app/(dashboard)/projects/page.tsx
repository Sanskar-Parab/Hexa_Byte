"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { FolderKanban, Route, Sparkles, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SectionHeader } from "@/components/ui/section-header";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingState } from "@/components/ui/loading-state";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { SkillAwareProject, AIGeneratedProjectDB, ProjectStats } from "@/types";

const DIFFICULTY_STEPS = ["BEGINNER", "INTERMEDIATE", "ADVANCED", "INDUSTRY"];

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<SkillAwareProject[]>([]);
  const [aiProjects, setAiProjects] = useState<AIGeneratedProjectDB[]>([]);
  const [userDifficulty, setUserDifficulty] = useState<string>("");
  const [preferredDifficulty, setPreferredDifficulty] = useState<string>("AUTO");
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [selectedCareerId, setSelectedCareerId] = useState<string | null>(null);
  const [projectStats, setProjectStats] = useState<ProjectStats | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const loadData = useCallback(async () => {
    let careerId = localStorage.getItem("selectedCareerId");

    try {
      const diffData = await api.getUserDifficulty().catch(() => null);
      if (diffData) {
        setUserDifficulty(diffData.user_difficulty);
        setPreferredDifficulty(diffData.preferred_difficulty || "AUTO");
      }

      let projectData = careerId ? await api.getProjectRecommendations(careerId).catch(() => null) : null;

      if (careerId && projectData === null) {
        // Stale career_id (e.g. left over from a reset dataset) - drop it and
        // fall back to the user's current top recommendation below.
        localStorage.removeItem("selectedCareerId");
        careerId = null;
      }

      if (!careerId) {
        const recs = await api.getStoredRecommendations().catch(() => []);
        if (recs.length > 0) {
          careerId = recs[0].career_id;
          localStorage.setItem("selectedCareerId", careerId);
          projectData = await api.getProjectRecommendations(careerId).catch(() => []);
        }
      }

      setSelectedCareerId(careerId);

      if (careerId) {
        setProjects(projectData || []);

        const aiData = await api.getAIGeneratedProjects(careerId).catch(() => []);
        setAiProjects(aiData);

        const stats = await api.getProjectStats(careerId).catch(() => null);
        setProjectStats(stats);
      }
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleGenerateAI = async () => {
    if (!selectedCareerId) return;
    setAiLoading(true);
    try {
      await api.generateAIProjects(selectedCareerId);
      await loadData();
    } catch {
    } finally {
      setAiLoading(false);
    }
  };

  const handleDifficultyChange = async (value: string) => {
    setPreferredDifficulty(value);
    try {
      await api.updatePreferredDifficulty(value);
      const diffData = await api.getUserDifficulty().catch(() => null);
      if (diffData) {
        setUserDifficulty(diffData.user_difficulty);
      }
      if (selectedCareerId) {
        const projectData = await api.getProjectRecommendations(selectedCareerId).catch(() => []);
        setProjects(projectData);
      }
    } catch {
    }
  };

  const handleProjectUpdate = useCallback(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return <LoadingState message="Finding projects that close your gaps..." />;
  }

  const allProjects = [
    ...projects.map((p) => ({ ...p, type: "database" as const })),
    ...aiProjects.map((p) => ({ ...p, type: "ai_generated" as const, is_ai_generated: true })),
  ];

  const filteredProjects = statusFilter === "all" ? allProjects : allProjects.filter((p) => p.status === statusFilter);
  const filteredDBProjects = filteredProjects.filter((p) => p.type === "database");
  const filteredAIProjects = filteredProjects.filter((p) => p.type === "ai_generated");

  const activeStepIndex = DIFFICULTY_STEPS.indexOf((userDifficulty || "BEGINNER").toUpperCase());

  return (
    <div className="max-w-6xl space-y-6">
      <SectionHeader
        eyebrow="Build"
        title="Projects That Build Your Skills"
        description="Projects are selected to close your current career gaps."
        action={
          selectedCareerId && (
            <Button onClick={handleGenerateAI} disabled={aiLoading} variant="outline">
              <Sparkles className={cn("mr-2 h-4 w-4", aiLoading && "animate-spin")} />
              {aiLoading ? "Generating..." : "AI Generate"}
            </Button>
          )
        }
      />

      {userDifficulty && (
        <Card>
          <CardContent className="flex flex-col gap-3 p-5">
            <p className="font-mono text-xs uppercase tracking-wide text-mute">Your Progression</p>
            <div className="flex items-center">
              {DIFFICULTY_STEPS.map((step, i) => (
                <div key={step} className="flex flex-1 items-center last:flex-initial">
                  <div className="flex flex-col items-center gap-1.5">
                    <div
                      className={cn(
                        "flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold",
                        i <= activeStepIndex ? "bg-ink text-white" : "bg-canvas-soft2 text-mute"
                      )}
                    >
                      {i + 1}
                    </div>
                    <span className={cn("text-[11px] font-medium", i <= activeStepIndex ? "text-ink" : "text-mute")}>
                      {step.charAt(0) + step.slice(1).toLowerCase()}
                    </span>
                  </div>
                  {i < DIFFICULTY_STEPS.length - 1 && (
                    <div className={cn("mx-2 h-0.5 flex-1 rounded-full", i < activeStepIndex ? "bg-ink" : "bg-hairline")} />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {projectStats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: "Total Projects", value: projectStats.total },
            { label: "In Progress", value: projectStats.in_progress },
            { label: "Completed", value: projectStats.completed },
            { label: "Not Started", value: projectStats.recommended },
          ].map((stat) => (
            <Card key={stat.label}>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-semibold tracking-tight text-ink">{stat.value}</div>
                <div className="mt-0.5 text-xs text-mute">{stat.label}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="flex flex-1 items-center gap-3 rounded-xl border border-hairline bg-canvas px-4 py-2.5">
          <span className="text-sm text-body whitespace-nowrap">Difficulty Level</span>
          <Select value={preferredDifficulty} onValueChange={handleDifficultyChange}>
            <SelectTrigger className="h-8 w-full sm:w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="AUTO">Auto (from skills)</SelectItem>
              <SelectItem value="BEGINNER">Beginner</SelectItem>
              <SelectItem value="INTERMEDIATE">Intermediate</SelectItem>
              <SelectItem value="ADVANCED">Advanced</SelectItem>
              <SelectItem value="INDUSTRY">Industry</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-hairline bg-canvas px-4 py-2.5">
          <Filter className="h-4 w-4 text-mute" />
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="h-8 w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Projects</SelectItem>
              <SelectItem value="recommended">Not Started</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {allProjects.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title="No projects yet"
          description={
            selectedCareerId
              ? "Generate your roadmap to receive project recommendations."
              : "Select a career and generate a roadmap to see recommended projects."
          }
          actionLabel={selectedCareerId ? "Go to Career Details" : "Browse Careers"}
          onAction={() => router.push(selectedCareerId ? `/careers/${selectedCareerId}` : "/careers")}
        />
      ) : (
        <>
          {filteredDBProjects.length > 0 && (
            <div>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-mute">Recommended Projects</h2>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {filteredDBProjects.map((project) => (
                  <ProjectCard key={project.id} project={project} onUpdate={handleProjectUpdate} />
                ))}
              </div>
            </div>
          )}

          {filteredAIProjects.length > 0 && (
            <div>
              <h2 className="mb-3 flex items-center gap-1.5 text-sm font-semibold uppercase tracking-wide text-mute">
                <Sparkles className="h-4 w-4 text-violet" />
                AI-Generated Projects
              </h2>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {filteredAIProjects.map((project) => (
                  <ProjectCard key={project.id} project={project} onUpdate={handleProjectUpdate} />
                ))}
              </div>
            </div>
          )}

          {filteredProjects.length === 0 && allProjects.length > 0 && (
            <EmptyState
              icon={Filter}
              title="No projects match this filter"
              description="Try selecting a different status filter."
            />
          )}
        </>
      )}
    </div>
  );
}
