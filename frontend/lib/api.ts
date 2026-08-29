const API_BASE = "/api";

async function fetcher<T>(url: string, options?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options?.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  return res.json();
}

export const api = {
  register: (name: string, email: string, password: string) =>
    fetcher<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    }),

  login: (email: string, password: string) =>
    fetcher<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  logout: () =>
    fetcher("/auth/logout", { method: "POST" }),

  getMe: () =>
    fetcher<any>("/auth/me"),

  getProfile: () =>
    fetcher<any>("/profile"),

  createProfile: (data: any) =>
    fetcher("/profile", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  completeOnboarding: (data: any) =>
    fetcher("/profile/onboarding", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getSkills: () =>
    fetcher<any[]>("/skills"),

  getUserSkills: () =>
    fetcher<any[]>("/skills/user"),

  addUserSkill: (skillId: string, proficiency: number) =>
    fetcher("/skills", {
      method: "POST",
      body: JSON.stringify({ skill_id: skillId, proficiency }),
    }),

  updateUserSkill: (userSkillId: string, proficiency: number, skillId?: string) =>
    fetcher(`/skills/${userSkillId}`, {
      method: "PUT",
      body: JSON.stringify({ skill_id: skillId || userSkillId, proficiency }),
    }),

  deleteUserSkill: (userSkillId: string) =>
    fetcher(`/skills/${userSkillId}`, { method: "DELETE" }),

  getInterests: () =>
    fetcher<any[]>("/interests"),

  getUserInterests: () =>
    fetcher<any[]>("/interests/user"),

  addUserInterest: (interestId: string) =>
    fetcher(`/interests/${interestId}`, { method: "POST" }),

  deleteUserInterest: (interestId: string) =>
    fetcher(`/interests/${interestId}`, { method: "DELETE" }),

  getAssessmentQuestions: () =>
    fetcher<any[]>("/assessment/questions"),

  submitAssessment: (answers: Record<string, number>) =>
    fetcher("/assessment/submit", {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),

  getAssessmentResult: () =>
    fetcher<any>("/assessment/result"),

  getCareers: () =>
    fetcher<any[]>("/careers"),

  getCareerDetail: (id: string) =>
    fetcher<any>(`/careers/${id}`),

  getCareerIntelligence: (id: string) =>
    fetcher<any>(`/careers/${id}/intelligence`),

  getRecommendations: () =>
    fetcher<any[]>("/careers/recommend", { method: "POST" }),

  getStoredRecommendations: () =>
    fetcher<any[]>("/careers/recommendations"),

  analyzeSkillGap: (careerId: string) =>
    fetcher<any>("/skill-gap/analyze", {
      method: "POST",
      body: JSON.stringify({ career_id: careerId }),
    }),

  generateRoadmap: (careerId: string) =>
    fetcher<any>("/roadmap/generate", {
      method: "POST",
      body: JSON.stringify({ career_id: careerId }),
    }),

  getRoadmap: (careerId?: string) => {
    const params = careerId ? `?career_id=${careerId}` : "";
    return fetcher<any>(`/roadmap${params}`);
  },

  updatePhaseStatus: (phaseId: string, status: string) =>
    fetcher(`/roadmap/phase/${phaseId}/status?status=${encodeURIComponent(status)}`, {
      method: "PUT",
    }),

  getProjectRecommendations: (careerId: string) =>
    fetcher<any[]>(`/projects/recommendations?career_id=${careerId}`),

  updateProjectStatus: (projectId: string, status: string) =>
    fetcher(`/projects/${projectId}/status?status=${encodeURIComponent(status)}`, {
      method: "POST",
    }),

  getDashboard: (careerId?: string) => {
    const params = careerId ? `?career_id=${careerId}` : "";
    return fetcher<any>(`/progress/dashboard${params}`);
  },

  updateProgress: (itemType: string, itemId: string, status: string) =>
    fetcher("/progress/update", {
      method: "POST",
      body: JSON.stringify({ item_type: itemType, item_id: itemId, status }),
    }),

  askCoach: (question: string, conversation?: { role: "user" | "assistant"; content: string }[]) =>
    fetcher<any>("/coach/ask", {
      method: "POST",
      body: JSON.stringify({ question, conversation: conversation || [] }),
    }),

  getCoachContext: () =>
    fetcher<any>("/coach/context"),

  startSkillAssessment: (skillId: string) =>
    fetcher<any>("/skill-assessment/start", {
      method: "POST",
      body: JSON.stringify({ skill_id: skillId }),
    }),

  checkAIStatus: () =>
    fetcher<{ available: boolean; error: string | null }>("/skill-assessment/ai-status"),

  submitSkillAssessment: (assessmentId: string, answers: { question_id: number; answer: string }[]) =>
    fetcher<any>("/skill-assessment/submit", {
      method: "POST",
      body: JSON.stringify({ assessment_id: assessmentId, answers }),
    }),

  loadDemo: () =>
    fetcher<any>("/demo/load", { method: "POST" }),

  getAllEvidence: () =>
    fetcher<any[]>("/evidence"),

  getSkillEvidence: (skillId: string) =>
    fetcher<any>(`/evidence/skill/${skillId}`),

  getNextBestAction: (careerId?: string) =>
    fetcher<any>("/next-best-action", {
      method: "POST",
      body: JSON.stringify({ career_id: careerId || null }),
    }),

  getUserDifficulty: () =>
    fetcher<any>("/projects/user-difficulty"),

  generateAIProjects: (careerId: string, count: number = 3) =>
    fetcher<any>("/projects/generate-ai", {
      method: "POST",
      body: JSON.stringify({ career_id: careerId, count }),
    }),

  updatePreferredDifficulty: (difficulty: string) =>
    fetcher<any>("/projects/preferred-difficulty", {
      method: "PUT",
      body: JSON.stringify({ difficulty }),
    }),

  getProjectStats: (careerId: string) =>
    fetcher<any>(`/projects/stats?career_id=${careerId}`),

  getAIGeneratedProjects: (careerId?: string) => {
    const params = careerId ? `?career_id=${careerId}` : "";
    return fetcher<any[]>(`/projects/ai-generated${params}`);
  },

  getProjectDetail: (projectId: string) =>
    fetcher<any>(`/projects/${projectId}`),

  uploadResume: (file: File) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const formData = new FormData();
    formData.append("file", file);
    return fetch(`${API_BASE}/resume/upload`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(error.detail || "Upload failed");
      }
      return res.json();
    });
  },

  getResumes: () =>
    fetcher<any[]>("/resume"),

  getResume: (id: string) =>
    fetcher<any>(`/resume/${id}`),

  deleteResume: (id: string) =>
    fetcher(`/resume/${id}`, { method: "DELETE" }),

  analyzeJob: (jobDescription: string) =>
    fetcher<any>("/job/analyze", {
      method: "POST",
      body: JSON.stringify({ job_description: jobDescription }),
    }),

  getJobHistory: () =>
    fetcher<any[]>("/job/history"),

  getJobAnalysis: (id: string) =>
    fetcher<any>(`/job/${id}`),

  deleteJobAnalysis: (id: string) =>
    fetcher(`/job/${id}`, { method: "DELETE" }),
};
