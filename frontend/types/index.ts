export interface User {
  id: string;
  email: string;
  name: string;
  is_demo: boolean;
  created_at: string;
}

export interface Profile {
  id: string;
  user_id: string;
  age_group: string;
  education_level: string;
  degree: string;
  branch: string;
  current_year: string;
  internship_experience: string;
  work_experience: string;
  projects_count: number;
  created_at: string;
  updated_at: string;
}

export interface Skill {
  id: string;
  name: string;
  category: string;
  description: string;
  beginner_definition: string;
  intermediate_definition: string;
  advanced_definition: string;
}

export interface UserSkill {
  id: string;
  skill_id: string;
  skill_name: string;
  proficiency: number;
  level_name: string | null;
  confidence: string | null;
  created_at: string;
}

export interface Interest {
  id: string;
  name: string;
  category: string;
}

export interface UserInterest {
  id: string;
  name: string;
  category: string;
}

export interface Career {
  id: string;
  name: string;
  description: string;
  category: string;
  required_skills: string[];
  optional_skills: string[];
  skill_importance: Record<string, number>;
  recommended_projects: string[];
  learning_sequence: any[];
  related_careers: string[];
}

export interface CareerRecommendation {
  id: string;
  career_id: string;
  career_name: string;
  match_score: number;
  confidence: string;
  why_it_matches: string[];
  strengths: string[];
  skill_gaps: string[];
  biggest_blocker: string | null;
  recommended_action: string | null;
  created_at: string;
}

export interface SkillDetail {
  skill_name: string;
  importance: number;
  user_proficiency: number;
  evidence_confidence: string;
  gap: number;
  status: "strong" | "developing" | "gap";
}

export interface UserSkillBrief {
  name: string;
  proficiency: number;
  confidence: string;
}

export interface CareerIntelligence {
  career_id: string;
  career_name: string;
  match_score: number;
  confidence: string;
  why_matches: string[];
  strengths: string[];
  skill_gaps: string[];
  biggest_blocker: string | null;
  recommended_action: string | null;
  skill_details: SkillDetail[];
  user_current_skills: UserSkillBrief[];
  learning_sequence: any[];
  description: string;
  required_skills: string[];
  optional_skills: string[];
}

export interface AssessmentQuestion {
  id: string;
  question_text: string;
  category: string;
  options: string[];
}

export interface AssessmentResult {
  scores: Record<string, number>;
  interpretation: Record<string, string>;
  top_interests: string[];
}

export interface SkillGapInfo {
  skill: string;
  current_level: number;
  target_level: number;
  gap_size: number;
  gap_severity: string;
  importance: number;
  priority_score: number;
}

export interface SkillGapAnalysis {
  career_name: string;
  career_id: string;
  total_skills_required: number;
  skills_with_data: number;
  overall_gap_score: number;
  gaps: SkillGapInfo[];
  high_priority: SkillGapInfo[];
  medium_priority: SkillGapInfo[];
  low_priority: SkillGapInfo[];
  summary: {
    total_gaps: number;
    high_count: number;
    medium_count: number;
    low_count: number;
  };
}

export interface Roadmap {
  id: string;
  career_id: string;
  career_name: string;
  summary: string;
  phases: RoadmapPhase[];
  created_at: string;
  updated_at: string | null;
}

export interface RoadmapPhase {
  id: string;
  phase_number: number;
  title: string;
  objective: string;
  skills: string[];
  activities: string[];
  project: string;
  duration_weeks: number;
  completion_criteria: string[];
  status: "not_started" | "in_progress" | "completed";
  adaptation_mode: "full" | "adapted" | "skipped";
  created_at: string | null;
  updated_at: string | null;
}

export interface Project {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  skills_developed: string[];
  expected_outcome: string;
  estimated_duration_weeks: number;
  portfolio_value: string;
}

export interface RecommendedProject {
  id: string;
  project: Project;
  career_id: string;
  match_score: number;
  covers_skills: string[];
  status: string;
}

export interface ProgressData {
  date: string;
  skills_mastered: number;
  projects_completed: number;
  assessment_score: number;
}

export interface DashboardData {
  overall_progress: number;
  readiness_score: {
    overall: number;
    technical_skills: number;
    project_completion: number;
    core_knowledge: number;
    communication: number;
  };
  phases: {
    total: number;
    completed: number;
    in_progress: number;
    items: any[];
  };
  projects: {
    total: number;
    completed: number;
    items: any[];
  };
  assessment_completed: boolean;
  roadmaps: any[];
  current_career_target?: string;
  top_skill_gaps?: any[];
  weekly_actions?: string[];
  recent_progress?: ProgressData[];
  career_readiness?: number;
}

export interface CoachResponse {
  response: string;
  source: string;
}

export interface SkillEvidence {
  id: string;
  source_type: string;
  source_id: string | null;
  title: string;
  description: string | null;
  score: number | null;
  confidence: string;
  metadata: Record<string, any> | null;
  created_at: string;
}

export interface SkillEvidenceResponse {
  skill_id: string;
  skill_name: string;
  proficiency: number;
  level_name: string | null;
  confidence: string;
  evidence: SkillEvidence[];
}

export interface NextBestAction {
  action: string | null;
  title: string;
  description: string;
  why: string;
  current: string | null;
  target: string | null;
  skill_name: string | null;
  priority_score: number;
  career_id: string | null;
  career_name: string | null;
  metadata: Record<string, any>;
  all_candidates: {
    action: string;
    title: string;
    score: number;
  }[];
}

export interface SkillAwareProject {
  id: string;
  project: Project;
  career_id: string;
  composite_score: number;
  career_relevance: number;
  gap_relevance: number;
  roadmap_relevance: number;
  difficulty_fit: number;
  covers_skills: string[];
  gap_skills_covered: string[];
  project_difficulty: string;
  user_difficulty: string;
  status: string;
  is_ai_generated: boolean;
}

export interface AIGeneratedProject {
  title: string;
  description: string;
  difficulty: string;
  why_this_project: string;
  skills_practiced: string[];
  skills_targeted: string[];
  duration: string;
  learning_objectives: string[];
  deliverables: string[];
  completion_criteria: string[];
}

export interface AIGeneratedProjectDB {
  id: string;
  user_id: string;
  career_id: string;
  title: string;
  description: string;
  difficulty: string;
  why_this_project: string;
  skills_practiced: string[];
  skills_targeted: string[];
  duration: string;
  learning_objectives: string[];
  deliverables: string[];
  completion_criteria: string[];
  status: string;
  created_at: string;
}

export interface ProjectStats {
  total: number;
  recommended: number;
  in_progress: number;
  completed: number;
}

export interface ResumeSkillItem {
  skill_name: string;
  skill_id: string | null;
  context: string;
}

export interface ResumeExtraction {
  skills: string[];
  projects: string[];
  experience: string[];
  education: string[];
  certifications: string[];
  technologies: string[];
  tools: string[];
}

export interface ResumeUploadResult {
  resume_id: string;
  filename: string;
  extraction: ResumeExtraction;
  matched_skills: ResumeSkillItem[];
  evidence_created: number;
  message: string;
}

export interface ResumeDetail {
  id: string;
  filename: string;
  extraction: ResumeExtraction;
  matched_skills: ResumeSkillItem[];
  extracted_at: string;
  created_at: string;
}

export interface JobSkillMatch {
  skill_name: string;
  status: "strong" | "developing" | "missing" | "not_demonstrated";
  user_proficiency: number;
  confidence: string | null;
  evidence_count: number;
  is_required: boolean;
}

export interface JobMatchResult {
  analysis_id: string;
  job_title: string;
  alignment_percentage: number;
  strong_skills: JobSkillMatch[];
  developing_skills: JobSkillMatch[];
  missing_skills: JobSkillMatch[];
  not_demonstrated: JobSkillMatch[];
  top_gap: string | null;
  next_action: string | null;
  evidence_created: number;
  required_skills_count: number;
  matched_count: number;
}

export interface JobAnalysisDetail {
  id: string;
  job_title: string;
  raw_text: string;
  required_skills: string[];
  preferred_skills: string[];
  experience_required: string | null;
  education_required: string | null;
  responsibilities: string[];
  technologies: string[];
  match_result: JobMatchResult | null;
  created_at: string;
}

export interface CoachContext {
  name: string | null;
  skills_count: number;
  has_profile: boolean;
  has_assessment: boolean;
  selected_career: string | null;
  career_match_score: number | null;
  has_roadmap: boolean;
  roadmap_progress: string | null;
  projects_completed: number;
  evidence_count: number;
  next_best_action: string | null;
  top_skill_gaps: { skill: string; gap: number }[];
}

export interface CoachAskResponse {
  response: string;
  source: "ai" | "fallback";
  suggestions: string[];
  context_used: {
    skills_count: number;
    has_career: boolean;
    has_roadmap: boolean;
    has_assessment: boolean;
    projects_completed: number;
    evidence_count: number;
  };
}
