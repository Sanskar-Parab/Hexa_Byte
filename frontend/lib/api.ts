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

  updateUserSkill: (userSkillId: string, proficiency: number) =>
    fetcher(`/skills/${userSkillId}`, {
      method: "PUT",
      body: JSON.stringify({ skill_id: userSkillId, proficiency }),
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
    fetcher(`/roadmap/phase/${phaseId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    }),

  getProjectRecommendations: (careerId: string) =>
    fetcher<any[]>(`/projects/recommendations?career_id=${careerId}`),

  updateProjectStatus: (projectId: string, status: string) =>
    fetcher(`/projects/${projectId}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    }),

  getDashboard: () =>
    fetcher<any>("/progress/dashboard"),

  updateProgress: (itemType: string, itemId: string, status: string) =>
    fetcher("/progress/update", {
      method: "POST",
      body: JSON.stringify({ item_type: itemType, item_id: itemId, status }),
    }),

  askCoach: (question: string) =>
    fetcher<any>("/coach/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  loadDemo: () =>
    fetcher<any>("/demo/load", { method: "POST" }),
};
