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

  getOpportunityRecommendations: (params?: {
    type?: "all" | "internship" | "job";
    limit?: number;
    minMatch?: number;
    careerId?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.type) query.set("type", params.type);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.minMatch) query.set("min_match", String(params.minMatch));
    if (params?.careerId) query.set("career_id", params.careerId);
    const qs = query.toString();
    return fetcher<import("@/types").OpportunityRecommendationsResponse>(
      `/opportunities/recommendations${qs ? `?${qs}` : ""}`
    );
  },

  getOutcomeTimeline: (trainingEnrollmentId?: string) => {
    const params = trainingEnrollmentId ? `?training_enrollment_id=${trainingEnrollmentId}` : "";
    return fetcher<import("@/types").OutcomeTimeline>(`/outcomes/timeline${params}`);
  },

  // --- Outcome reporting (student-facing write flow) ----------------------

  getOutcomeConsent: () =>
    fetcher<import("@/types").OutcomeConsentState>("/outcomes/consent"),

  submitOutcomeConsent: (consented: boolean) =>
    fetcher<import("@/types").OutcomeConsentState>("/outcomes/consent", {
      method: "POST",
      body: JSON.stringify({ consented }),
    }),

  listTrainingPrograms: () =>
    fetcher<import("@/types").TrainingProgram[]>("/outcomes/training"),

  listEnrollments: () =>
    fetcher<import("@/types").TrainingEnrollment[]>("/outcomes/enrollment"),

  createEnrollment: (trainingProgramId: string) =>
    fetcher<import("@/types").TrainingEnrollment>("/outcomes/enrollment", {
      method: "POST",
      body: JSON.stringify({ training_program_id: trainingProgramId }),
    }),

  listEmploymentOutcomes: () =>
    fetcher<import("@/types").EmploymentOutcome[]>("/outcomes/employment"),

  createEmploymentOutcome: (data: {
    training_enrollment_id?: string;
    employment_status: string;
    employment_type?: string;
    company_name?: string;
    job_title?: string;
    location?: string;
    employment_start_date?: string;
    salary?: number;
    salary_currency?: string;
    salary_period?: string;
  }) =>
    fetcher<import("@/types").EmploymentOutcome>("/outcomes/employment", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  createCheckIn: (data: {
    employment_outcome_id: string;
    employment_status: string;
    company_name?: string;
    job_title?: string;
    salary?: number;
    salary_currency?: string;
    still_employed?: boolean;
    reason_for_leaving?: string;
    notes?: string;
  }) =>
    fetcher<import("@/types").OutcomeCheckInEntry>("/outcomes/check-in", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  submitOutcomeEvidence: (outcomeId: string) =>
    fetcher<import("@/types").EmploymentOutcome>(`/outcomes/employment/${outcomeId}/evidence`, {
      method: "PATCH",
    }),

  // --- Admin verification (admin-only) -----------------------------------

  getAdminEmploymentOutcomes: (params?: { limit?: number; offset?: number; employment_status?: string }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    if (params?.employment_status) q.set("employment_status", params.employment_status);
    const qs = q.toString();
    return fetcher<import("@/types").EmploymentOutcome[]>(`/admin/outcomes/employment${qs ? `?${qs}` : ""}`);
  },

  verifyOutcome: (outcomeId: string) =>
    fetcher<import("@/types").EmploymentOutcome>(`/admin/outcomes/${outcomeId}/verify`, {
      method: "PATCH",
    }),

  // --- Admin/government skilling-impact analytics (admin-only) -----------

  getAdminOverview: (filters?: import("@/types").AdminAnalyticsFilters) =>
    fetcher<import("@/types").CohortMetrics>(`/admin/outcomes/overview${adminFilterQuery(filters)}`),

  getAdminProviders: (filters?: import("@/types").AdminAnalyticsFilters) =>
    fetcher<import("@/types").ProviderComparisonRow[]>(`/admin/outcomes/providers${adminFilterQuery(filters)}`),

  getAdminPrograms: (filters?: import("@/types").AdminAnalyticsFilters) =>
    fetcher<import("@/types").ProgramAnalyticsRow[]>(`/admin/outcomes/programs${adminFilterQuery(filters)}`),

  getAdminSkillGaps: (filters?: import("@/types").AdminAnalyticsFilters) =>
    fetcher<import("@/types").SkillGapRow[]>(`/admin/outcomes/skill-gaps${adminFilterQuery(filters)}`),

  getAdminNonPlacement: (filters?: import("@/types").AdminAnalyticsFilters) =>
    fetcher<import("@/types").NonPlacementCategoryRow[]>(`/admin/outcomes/non-placement${adminFilterQuery(filters)}`),

  getAdminFilterOptions: () =>
    fetcher<import("@/types").AdminFilterOptions>("/admin/outcomes/filters"),

  getAdminCurriculumRecommendations: (filters?: import("@/types").AdminAnalyticsFilters) =>
    fetcher<import("@/types").CurriculumRecommendationRow[]>(
      `/admin/outcomes/curriculum-recommendations${adminFilterQuery(filters)}`
    ),

  loadAdminDemoData: () =>
    fetcher<{ message: string; created: boolean; trainees_created: number }>("/admin/outcomes/demo-data", {
      method: "POST",
    }),

  // --- Trainee Identity Resolution (SIH 26135) ---

  listMasters: (params?: { page?: number; page_size?: number; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set("page", String(params.page));
    if (params?.page_size) q.set("page_size", String(params.page_size));
    if (params?.search) q.set("search", params.search);
    const qs = q.toString();
    return fetcher<import("@/types").ListMastersResponse>(`/admin/trainees${qs ? `?${qs}` : ""}`);
  },

  getMasterDetail: (masterId: string) =>
    fetcher<import("@/types").MasterTraineeDetail>(`/admin/trainees/${masterId}`),

  previewTraineeMatch: (data: { trainee_name: string; dob: string; phone?: string; program_name: string; program_trainee_id: string }) =>
    fetcher<import("@/types").MatchResult>("/admin/trainees/match-preview", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  createTraineeRecord: (data: { trainee_name: string; dob: string; phone?: string; program_name: string; program_trainee_id: string }) =>
    fetcher<import("@/types").CreateTraineeResponse>("/admin/trainees", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listIdentityReviews: (params?: { status?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.page) q.set("page", String(params.page));
    if (params?.page_size) q.set("page_size", String(params.page_size));
    const qs = q.toString();
    return fetcher<import("@/types").ListReviewsResponse>(`/admin/identity-reviews${qs ? `?${qs}` : ""}`);
  },

  getIdentityReview: (reviewId: string) =>
    fetcher<import("@/types").IdentityReview>(`/admin/identity-reviews/${reviewId}`),

  decideIdentityReview: (reviewId: string, decision: "link" | "reject") =>
    fetcher<{ review: any; master: any; record: any; message: string }>(`/admin/identity-reviews/${reviewId}`, {
      method: "PATCH",
      body: JSON.stringify({ decision }),
    }),
};

function adminFilterQuery(filters?: import("@/types").AdminAnalyticsFilters): string {
  if (!filters) return "";
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}
