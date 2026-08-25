"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { FolderKanban, Route, Sparkles, BarChart3, CheckCircle2, Clock, TrendingUp, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { api } from "@/lib/api";
import { SkillAwareProject, AIGeneratedProjectDB, ProjectStats } from "@/types";

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
    const careerId = localStorage.getItem("selectedCareerId");
    setSelectedCareerId(careerId);

    try {
      const diffData = await api.getUserDifficulty().catch(() => null);
      if (diffData) {
        setUserDifficulty(diffData.user_difficulty);
        setPreferredDifficulty(diffData.preferred_difficulty || "AUTO");
      }

      if (careerId) {
        const projectData = await api.getProjectRecommendations(careerId).catch(() => []);
        setProjects(projectData);

        const aiData = await api.getAIGeneratedProjects(careerId).catch(() => []);
        setAiProjects(aiData);

        const stats = await api.getProjectStats(careerId).catch(() => null);
        setProjectStats(stats);
      } else {
        const recs = await api.getStoredRecommendations().catch(() => []);
        if (recs.length > 0) {
          const topCareerId = recs[0].career_id;
          localStorage.setItem("selectedCareerId", topCareerId);
          setSelectedCareerId(topCareerId);
          const projectData = await api.getProjectRecommendations(topCareerId).catch(() => []);
          setProjects(projectData);

          const aiData = await api.getAIGeneratedProjects(topCareerId).catch(() => []);
          setAiProjects(aiData);

          const stats = await api.getProjectStats(topCareerId).catch(() => null);
          setProjectStats(stats);
        }
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
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  const DIFFICULTY_COLORS: Record<string, string> = {
    BEGINNER: "bg-green-100 text-green-800",
    INTERMEDIATE: "bg-blue-100 text-blue-800",
    ADVANCED: "bg-purple-100 text-purple-800",
    INDUSTRY: "bg-amber-100 text-amber-800",
  };

  const allProjects = [
    ...projects.map(p => ({ ...p, type: "database" as const })),
    ...aiProjects.map(p => ({ ...p, type: "ai_generated" as const, is_ai_generated: true })),
  ];

  const filteredProjects = statusFilter === "all"
    ? allProjects
    : allProjects.filter(p => p.status === statusFilter);

  const filteredDBProjects = filteredProjects.filter(p => p.type === "database");
  const filteredAIProjects = filteredProjects.filter(p => p.type === "ai_generated");

  return (
    <div className="max-w-6xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Recommended Projects</h1>
          <p className="text-slate-600 mt-1">
            Build your portfolio with projects matched to your goals and skill gaps.
          </p>
        </div>
        {selectedCareerId && (
          <Button onClick={handleGenerateAI} disabled={aiLoading} variant="outline">
            <Sparkles className={`mr-2 h-4 w-4 ${aiLoading ? "animate-spin" : ""}`} />
            {aiLoading ? "Generating..." : "AI Generate"}
          </Button>
        )}
      </div>

      {projectStats && (
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-100">
          <CardContent className="p-4">
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-900">{projectStats.total}</div>
                <div className="text-xs text-slate-500">Total Projects</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{projectStats.in_progress}</div>
                <div className="text-xs text-slate-500">In Progress</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-600">{projectStats.completed}</div>
                <div className="text-xs text-slate-500">Completed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-600">{projectStats.recommended}</div>
                <div className="text-xs text-slate-500">Not Started</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-4">
        <Card className="bg-slate-50 flex-1">
          <CardContent className="p-3 flex items-center gap-3">
            <BarChart3 className="h-5 w-5 text-slate-500" />
            <span className="text-sm text-slate-600">Difficulty Level:</span>
            <Select value={preferredDifficulty} onValueChange={handleDifficultyChange}>
              <SelectTrigger className="w-[180px] h-8">
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
          </CardContent>
        </Card>

        <Card className="bg-slate-50">
          <CardContent className="p-3 flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-500" />
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px] h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Projects</SelectItem>
                <SelectItem value="recommended">Not Started</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
      </div>

      {allProjects.length === 0 ? (
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
        <>
          {filteredDBProjects.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-slate-900 mb-3">Database Projects</h2>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredDBProjects.map((project) => (
                  <ProjectCard key={project.id} project={project} onUpdate={handleProjectUpdate} />
                ))}
              </div>
            </div>
          )}

          {filteredAIProjects.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-slate-900 mb-3">
                <Sparkles className="inline h-4 w-4 mr-1 text-amber-500" />
                AI-Generated Projects
              </h2>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredAIProjects.map((project) => (
                  <ProjectCard key={project.id} project={project} onUpdate={handleProjectUpdate} />
                ))}
              </div>
            </div>
          )}

          {filteredProjects.length === 0 && allProjects.length > 0 && (
            <div className="text-center py-12">
              <Filter className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <h2 className="text-lg font-semibold text-slate-900">No projects match this filter</h2>
              <p className="text-slate-600 mt-1">Try selecting a different status filter.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
