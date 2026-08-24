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
  created_at: string;
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
