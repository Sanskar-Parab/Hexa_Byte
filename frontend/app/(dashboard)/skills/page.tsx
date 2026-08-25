"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { SkillSelector } from "@/components/skills/SkillSelector";
import { SkillAssessment } from "@/components/skills/SkillAssessment";
import { api } from "@/lib/api";
import { Brain, Settings, ChevronDown, ChevronUp, ShieldCheck, ShieldAlert, ShieldX, FileText, CheckCircle2 } from "lucide-react";

interface UserSkill {
  id: string;
  skill_id: string;
  skill_name: string;
  proficiency: number;
  level_name: string | null;
  confidence: string | null;
}

interface SkillEvidence {
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

const PROFICIENCY_LABELS: Record<number, string> = {
  1: "Beginner",
  2: "Basic",
  3: "Intermediate",
  4: "Advanced",
  5: "Expert",
};

const CONFIDENCE_CONFIG: Record<string, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
  HIGH: {
    label: "High",
    color: "text-emerald-700",
    bg: "bg-emerald-50 border-emerald-200",
    icon: <ShieldCheck className="h-3.5 w-3.5" />,
  },
  MEDIUM: {
    label: "Medium",
    color: "text-amber-700",
    bg: "bg-amber-50 border-amber-200",
    icon: <ShieldAlert className="h-3.5 w-3.5" />,
  },
  LOW: {
    label: "Low",
    color: "text-rose-700",
    bg: "bg-rose-50 border-rose-200",
    icon: <ShieldX className="h-3.5 w-3.5" />,
  },
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  assessment: "AI Skill Assessment",
  manual: "Manual Declaration",
  project: "Completed Project",
  resume: "Resume",
  job: "Job Experience",
  practical: "Practical Experience",
};

export default function SkillsPage() {
  const [userSkills, setUserSkills] = useState<UserSkill[]>([]);
  const [allSkills, setAllSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [assessingSkill, setAssessingSkill] = useState<{ id: string; name: string } | null>(null);
  const [manualEditSkill, setManualEditSkill] = useState<string | null>(null);
  const [showManualSection, setShowManualSection] = useState(false);
  const [expandedSkills, setExpandedSkills] = useState<Set<string>>(new Set());
  const [evidenceData, setEvidenceData] = useState<Record<string, SkillEvidence[]>>({});

  useEffect(() => {
    Promise.all([api.getUserSkills(), api.getSkills()])
      .then(([skills, all]) => {
        setUserSkills(skills);
        setAllSkills(all);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const refreshSkills = async () => {
    try {
      const skills = await api.getUserSkills();
      setUserSkills(skills);
    } catch {}
  };

  const toggleEvidence = async (skillId: string) => {
    const newExpanded = new Set(expandedSkills);
    if (newExpanded.has(skillId)) {
      newExpanded.delete(skillId);
    } else {
      newExpanded.add(skillId);
      if (!evidenceData[skillId]) {
        try {
          const data = await api.getSkillEvidence(skillId);
          setEvidenceData((prev) => ({ ...prev, [skillId]: data.evidence || [] }));
        } catch {
          setEvidenceData((prev) => ({ ...prev, [skillId]: [] }));
        }
      }
    }
    setExpandedSkills(newExpanded);
  };

  const handleAddSkill = async (skillId: string, proficiency: number) => {
    try {
      await api.addUserSkill(skillId, proficiency);
      await refreshSkills();
    } catch {}
  };

  const handleRemoveSkill = async (skillId: string) => {
    const userSkill = userSkills.find((s) => s.skill_id === skillId);
    if (userSkill?.id) {
      try {
        await api.deleteUserSkill(userSkill.id);
        setUserSkills(userSkills.filter((s) => s.skill_id !== skillId));
      } catch {}
    }
  };

  const handleUpdateProficiency = async (skillId: string, proficiency: number) => {
    const userSkill = userSkills.find((s) => s.skill_id === skillId);
    if (userSkill?.id) {
      try {
        await api.updateUserSkill(userSkill.id, proficiency, skillId);
        setUserSkills(userSkills.map((s) =>
          s.skill_id === skillId ? { ...s, proficiency } : s
        ));
      } catch {}
    }
    setManualEditSkill(null);
  };

  const handleAssessmentComplete = () => {
    setAssessingSkill(null);
    refreshSkills();
  };

  const getSkillName = (skillId: string) => {
    const skill = allSkills.find((s) => s.id === skillId);
    return skill?.name || "Unknown Skill";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (assessingSkill) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <SkillAssessment
          skillId={assessingSkill.id}
          skillName={assessingSkill.name}
          onComplete={handleAssessmentComplete}
          onCancel={() => setAssessingSkill(null)}
        />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Skills</h1>
        <p className="text-slate-600 mt-1">Manage your skills, proficiency levels, and evidence.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Skills Overview</CardTitle>
        </CardHeader>
        <CardContent>
          {userSkills.length === 0 ? (
            <p className="text-sm text-slate-500">No skills added yet. Use the selector below to add your first skill.</p>
          ) : (
            <div className="grid sm:grid-cols-2 gap-3">
              {userSkills.map((skill) => {
                const isEditing = manualEditSkill === skill.skill_id;
                const isExpanded = expandedSkills.has(skill.skill_id);
                const confidence = skill.confidence || "LOW";
                const conf = CONFIDENCE_CONFIG[confidence] || CONFIDENCE_CONFIG.LOW;
                const levelName = skill.level_name || PROFICIENCY_LABELS[skill.proficiency] || "Not assessed";
                const skillEvidence = evidenceData[skill.skill_id] || [];

                return (
                  <div key={skill.skill_id} className="rounded-lg border p-3 bg-white space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-900">{skill.skill_name}</p>
                        <p className="text-xs text-slate-500">
                          {levelName} — {skill.proficiency}/5
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {[1, 2, 3, 4, 5].map((level) => (
                          <div
                            key={level}
                            className={`h-2.5 w-2.5 rounded-full ${
                              level <= skill.proficiency ? "bg-blue-500" : "bg-slate-200"
                            }`}
                          />
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border ${conf.bg} ${conf.color}`}>
                        {conf.icon}
                        Confidence: {conf.label}
                      </span>
                    </div>

                    {isEditing ? (
                      <div className="space-y-2 pt-1">
                        <Slider
                          value={[skill.proficiency]}
                          min={1}
                          max={5}
                          step={1}
                          onValueChange={([v]) => {
                            setUserSkills(userSkills.map((s) =>
                              s.skill_id === skill.skill_id ? { ...s, proficiency: v } : s
                            ));
                          }}
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            className="h-7 text-xs"
                            onClick={() => handleUpdateProficiency(skill.skill_id, skill.proficiency)}
                          >
                            Save
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs"
                            onClick={() => {
                              setManualEditSkill(null);
                              refreshSkills();
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-2 pt-1">
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs"
                          onClick={() => setAssessingSkill({ id: skill.skill_id, name: skill.skill_name })}
                        >
                          <Brain className="h-3 w-3 mr-1" />
                          Assess Level
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs"
                          onClick={() => setManualEditSkill(skill.skill_id)}
                        >
                          <Settings className="h-3 w-3 mr-1" />
                          Set Manually
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs"
                          onClick={() => toggleEvidence(skill.skill_id)}
                        >
                          <FileText className="h-3 w-3 mr-1" />
                          Evidence
                          {isExpanded ? <ChevronUp className="h-3 w-3 ml-0.5" /> : <ChevronDown className="h-3 w-3 ml-0.5" />}
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs text-rose-500"
                          onClick={() => handleRemoveSkill(skill.skill_id)}
                        >
                          Remove
                        </Button>
                      </div>
                    )}

                    {isExpanded && (
                      <div className="pt-2 border-t border-slate-100 space-y-2">
                        <p className="text-xs font-medium text-slate-600">Evidence ({skillEvidence.length})</p>
                        {skillEvidence.length === 0 ? (
                          <p className="text-xs text-slate-400">No evidence recorded yet.</p>
                        ) : (
                          <div className="space-y-1.5">
                            {skillEvidence.map((ev) => {
                              const evConf = CONFIDENCE_CONFIG[ev.confidence] || CONFIDENCE_CONFIG.LOW;
                              return (
                                <div key={ev.id} className="rounded-md bg-slate-50 p-2 text-xs space-y-1">
                                  <div className="flex items-center justify-between">
                                    <span className="font-medium text-slate-700">
                                      {SOURCE_TYPE_LABELS[ev.source_type] || ev.source_type}
                                    </span>
                                    <span className={`inline-flex items-center gap-0.5 font-medium ${evConf.color}`}>
                                      {evConf.icon}
                                      {evConf.label}
                                    </span>
                                  </div>
                                  {ev.description && (
                                    <p className="text-slate-500">{ev.description}</p>
                                  )}
                                  {ev.score !== null && ev.score !== undefined && (
                                    <div className="flex items-center gap-1">
                                      <CheckCircle2 className="h-3 w-3 text-blue-500" />
                                      <span className="text-slate-600">Score: {Math.round(ev.score)}%</span>
                                    </div>
                                  )}
                                  <p className="text-slate-400">
                                    {new Date(ev.created_at).toLocaleDateString("en-US", {
                                      year: "numeric",
                                      month: "short",
                                      day: "numeric",
                                    })}
                                  </p>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Add & Update Skills</CardTitle>
        </CardHeader>
        <CardContent>
          <SkillSelector
            availableSkills={allSkills}
            selectedSkills={userSkills.map((s) => ({
              skill: allSkills.find((as) => as.id === s.skill_id) || { id: s.skill_id, name: s.skill_name, category: "" },
              proficiency: s.proficiency,
            }))}
            onAdd={handleAddSkill}
            onRemove={handleRemoveSkill}
            onUpdateProficiency={handleUpdateProficiency}
          />
        </CardContent>
      </Card>
    </div>
  );
}
