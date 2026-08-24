"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SkillSelector } from "@/components/skills/SkillSelector";
import { api } from "@/lib/api";

interface UserSkill {
  id: string;
  skill_id: string;
  skill_name: string;
  proficiency: number;
}

export default function SkillsPage() {
  const [userSkills, setUserSkills] = useState<UserSkill[]>([]);
  const [allSkills, setAllSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getUserSkills(), api.getSkills()])
      .then(([skills, all]) => {
        setUserSkills(skills);
        setAllSkills(all);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleAddSkill = async (skillId: string, proficiency: number) => {
    try {
      await api.addUserSkill(skillId, proficiency);
      const skill = allSkills.find((s) => s.id === skillId);
      if (skill && !userSkills.find((s) => s.skill_id === skillId)) {
        setUserSkills([...userSkills, { id: "", skill_id: skillId, skill_name: skill.name, proficiency }]);
      }
    } catch {}
  };

  const handleRemoveSkill = async (skillId: string) => {
    const userSkill = userSkills.find((s) => s.skill_id === skillId);
    if (userSkill?.id) {
      try {
        await api.deleteUserSkill(userSkill.id);
      } catch {}
    }
    setUserSkills(userSkills.filter((s) => s.skill_id !== skillId));
  };

  const handleUpdateProficiency = (skillId: string, proficiency: number) => {
    setUserSkills(userSkills.map((s) => (s.skill_id === skillId ? { ...s, proficiency } : s)));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Skills</h1>
        <p className="text-slate-600 mt-1">Manage your skills and proficiency levels.</p>
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
              {userSkills.map((skill) => (
                <div key={skill.skill_id} className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{skill.skill_name}</p>
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
              ))}
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
