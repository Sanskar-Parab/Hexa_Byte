"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { SkillSelector } from "@/components/skills/SkillSelector";
import { SkillAssessment } from "@/components/skills/SkillAssessment";
import { SectionHeader } from "@/components/ui/section-header";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingState } from "@/components/ui/loading-state";
import { ConfidenceBadge } from "@/components/ui/status-badge";
import { EvidenceBadge } from "@/components/ui/evidence-badge";
import { SkillBar } from "@/components/ui/skill-bar";
import { api } from "@/lib/api";
import { Brain, Settings, ChevronDown, ChevronUp, FileText, ArrowRight, Compass, CheckCircle2 } from "lucide-react";

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

export default function SkillsPage() {
  const [userSkills, setUserSkills] = useState<UserSkill[]>([]);
  const [allSkills, setAllSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [assessingSkill, setAssessingSkill] = useState<{ id: string; name: string } | null>(null);
  const [manualEditSkill, setManualEditSkill] = useState<string | null>(null);
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

  if (loading) {
    return <LoadingState message="Analyzing your skills..." />;
  }

  if (assessingSkill) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
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
    <div className="max-w-5xl mx-auto space-y-8">
      <SectionHeader
        eyebrow="Skill Intelligence"
        title="Your Skill Profile"
        description="Your skills are based on what you can demonstrate, not just what you claim."
      />

      {userSkills.length === 0 ? (
        <EmptyState
          icon={Compass}
          title="No skills tracked yet"
          description="Add your first skill below, or take the AI assessment to get an evidence-backed proficiency score."
        />
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {userSkills.map((skill) => {
            const isEditing = manualEditSkill === skill.skill_id;
            const isExpanded = expandedSkills.has(skill.skill_id);
            const confidence = skill.confidence || "LOW";
            const levelName = skill.level_name || PROFICIENCY_LABELS[skill.proficiency] || "Not assessed";
            const skillEvidence = evidenceData[skill.skill_id] || [];

            return (
              <div key={skill.skill_id} className="rounded-xl border border-hairline bg-canvas p-5 shadow-card space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-ink">{skill.skill_name}</p>
                    <p className="text-xs text-mute mt-0.5">
                      {levelName} · {skill.proficiency}/5
                    </p>
                  </div>
                  <ConfidenceBadge confidence={confidence} />
                </div>

                <SkillBar proficiency={skill.proficiency} />

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
                  <div className="flex flex-wrap items-center gap-2 pt-1">
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
                    <Link href={`/skills/${skill.skill_id}`} className="ml-auto">
                      <Button size="sm" variant="ghost" className="h-7 text-xs">
                        View Skill
                        <ArrowRight className="h-3 w-3 ml-1" />
                      </Button>
                    </Link>
                  </div>
                )}

                {isExpanded && (
                  <div className="pt-3 border-t border-hairline space-y-2">
                    <p className="text-xs font-medium text-body">Evidence ({skillEvidence.length})</p>
                    {skillEvidence.length === 0 ? (
                      <p className="text-xs text-mute">No evidence recorded yet.</p>
                    ) : (
                      <div className="space-y-2">
                        {skillEvidence.map((ev) => (
                          <div key={ev.id} className="flex items-start justify-between gap-2 rounded-lg bg-canvas-soft p-2.5 text-xs">
                            <div className="space-y-1">
                              <EvidenceBadge sourceType={ev.source_type} />
                              {ev.description && <p className="text-body">{ev.description}</p>}
                              {ev.score !== null && ev.score !== undefined && (
                                <div className="flex items-center gap-1 text-mute">
                                  <CheckCircle2 className="h-3 w-3 text-link" />
                                  Score: {Math.round(ev.score)}%
                                </div>
                              )}
                            </div>
                            <span className="shrink-0 text-mute">
                              {new Date(ev.created_at).toLocaleDateString("en-US", {
                                month: "short",
                                day: "numeric",
                              })}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {!isEditing && (
                  <button
                    onClick={() => handleRemoveSkill(skill.skill_id)}
                    className="text-xs text-err hover:underline"
                  >
                    Remove skill
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

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
