"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ArrowLeft, Loader2, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { SkillSelector } from "@/components/skills/SkillSelector";

const steps = ["Basic Info", "Experience", "Interests", "Skills"];

const selectClass =
  "w-full rounded-lg border border-hairline bg-canvas px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-ring";
const textareaClass =
  "w-full min-h-[90px] rounded-lg border border-hairline bg-canvas px-3 py-2 text-sm text-ink placeholder:text-mute focus:outline-none focus:ring-2 focus:ring-ring";
const labelClass = "mb-1.5 block text-sm font-medium text-body";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);

  const [profile, setProfile] = useState({
    age_group: "",
    education_level: "",
    degree: "",
    branch: "",
    current_year: "",
    internship_experience: "",
    work_experience: "",
    projects_count: 0,
  });

  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [allInterests, setAllInterests] = useState<any[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<{ name: string; proficiency: number }[]>([]);
  const [allSkills, setAllSkills] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([api.getInterests(), api.getSkills()])
      .then(([interestsData, skillsData]) => {
        setAllInterests(interestsData);
        setAllSkills(skillsData);
      })
      .catch(() => {});
  }, []);

  const handleToggleInterest = (interestId: string) => {
    setSelectedInterests((prev) =>
      prev.includes(interestId)
        ? prev.filter((id) => id !== interestId)
        : [...prev, interestId]
    );
  };

  const handleAddSkill = (skillId: string, proficiency: number) => {
    const skill = allSkills.find((s) => s.id === skillId);
    if (skill && !selectedSkills.find((s) => s.name === skill.name)) {
      setSelectedSkills([...selectedSkills, { name: skill.name, proficiency }]);
    }
  };

  const handleRemoveSkill = (skillName: string) => {
    setSelectedSkills(selectedSkills.filter((s) => s.name !== skillName));
  };

  const handleUpdateProficiency = (skillName: string, proficiency: number) => {
    setSelectedSkills(selectedSkills.map((s) => (s.name === skillName ? { ...s, proficiency } : s)));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const interestNames = selectedInterests
        .map((id) => allInterests.find((i) => i.id === id)?.name)
        .filter(Boolean);

      await api.completeOnboarding({
        profile,
        skills: selectedSkills.map((s) => ({ name: s.name, proficiency: s.proficiency })),
        interests: interestNames,
      });
      router.push("/assessment");
    } catch {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <p className="mb-2 font-mono text-xs uppercase tracking-wider text-mute">Get set up</p>
        <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">Profile setup</h1>
        <p className="mt-1.5 text-sm text-body">
          Tell us about yourself so Next Path AI can build recommendations around real context, not guesses.
        </p>
      </div>

      <div className="flex items-center">
        {steps.map((s, i) => (
          <div key={s} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-2">
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-full font-mono text-xs font-medium transition-colors ${
                  i < step
                    ? "bg-ink text-white"
                    : i === step
                    ? "bg-ink text-white ring-4 ring-canvas-soft2"
                    : "bg-canvas-soft2 text-mute"
                }`}
              >
                {i < step ? <Check className="h-4 w-4" /> : String(i + 1).padStart(2, "0")}
              </div>
              <span className={`hidden text-xs font-medium sm:block ${i === step ? "text-ink" : "text-mute"}`}>
                {s}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`mx-2 h-px flex-1 ${i < step ? "bg-ink" : "bg-hairline"}`} />
            )}
          </div>
        ))}
      </div>

      <Card className="shadow-panel">
        <CardContent className="p-6 sm:p-8">
          {step === 0 && (
            <div className="space-y-5">
              <h3 className="text-lg font-semibold text-ink">Basic information</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className={labelClass}>Age Group</label>
                  <select
                    value={profile.age_group}
                    onChange={(e) => setProfile({ ...profile, age_group: e.target.value })}
                    className={selectClass}
                  >
                    <option value="">Select...</option>
                    <option value="14-17">14-17</option>
                    <option value="18-22">18-22</option>
                    <option value="23-27">23-27</option>
                    <option value="28+">28+</option>
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Education Level</label>
                  <select
                    value={profile.education_level}
                    onChange={(e) => setProfile({ ...profile, education_level: e.target.value })}
                    className={selectClass}
                  >
                    <option value="">Select...</option>
                    <option value="High School">High School</option>
                    <option value="Bachelor's">Bachelor&apos;s Degree</option>
                    <option value="Master's">Master&apos;s Degree</option>
                    <option value="PhD">PhD</option>
                    <option value="Self-taught">Self-taught</option>
                  </select>
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className={labelClass}>Degree / Program</label>
                  <Input
                    value={profile.degree}
                    onChange={(e) => setProfile({ ...profile, degree: e.target.value })}
                    placeholder="e.g., B.Tech, BCA, B.Sc"
                  />
                </div>
                <div>
                  <label className={labelClass}>Branch / Field</label>
                  <Input
                    value={profile.branch}
                    onChange={(e) => setProfile({ ...profile, branch: e.target.value })}
                    placeholder="e.g., Computer Science"
                  />
                </div>
              </div>
              <div>
                <label className={labelClass}>Current Year</label>
                <select
                  value={profile.current_year}
                  onChange={(e) => setProfile({ ...profile, current_year: e.target.value })}
                  className={selectClass}
                >
                  <option value="">Select...</option>
                  <option value="1st Year">1st Year</option>
                  <option value="2nd Year">2nd Year</option>
                  <option value="3rd Year">3rd Year</option>
                  <option value="4th Year">4th Year</option>
                  <option value="Graduated">Graduated</option>
                </select>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-5">
              <h3 className="text-lg font-semibold text-ink">Experience</h3>
              <div>
                <label className={labelClass}>Internship Experience</label>
                <textarea
                  value={profile.internship_experience}
                  onChange={(e) => setProfile({ ...profile, internship_experience: e.target.value })}
                  placeholder="Describe any internships you've completed..."
                  className={textareaClass}
                />
              </div>
              <div>
                <label className={labelClass}>Work Experience</label>
                <textarea
                  value={profile.work_experience}
                  onChange={(e) => setProfile({ ...profile, work_experience: e.target.value })}
                  placeholder="Describe any work experience..."
                  className={textareaClass}
                />
              </div>
              <div>
                <label className={labelClass}>Number of Projects: {profile.projects_count}</label>
                <input
                  type="range"
                  min={0}
                  max={20}
                  value={profile.projects_count}
                  onChange={(e) => setProfile({ ...profile, projects_count: Number(e.target.value) })}
                  className="w-full accent-ink"
                />
                <div className="mt-1 flex justify-between text-xs text-mute">
                  <span>0</span>
                  <span>20+</span>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-ink">Interests</h3>
              <p className="text-sm text-body">Select areas that interest you:</p>
              <div className="flex flex-wrap gap-2">
                {allInterests.map((interest) => {
                  const selected = selectedInterests.includes(interest.id);
                  return (
                    <button
                      key={interest.id}
                      onClick={() => handleToggleInterest(interest.id)}
                      className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                        selected
                          ? "border-ink bg-ink text-white"
                          : "border-hairline text-body hover:border-hairline-strong hover:bg-canvas-soft"
                      }`}
                    >
                      {interest.name}
                    </button>
                  );
                })}
              </div>
              {selectedInterests.length > 0 && (
                <p className="text-sm text-mute">{selectedInterests.length} interests selected</p>
              )}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-ink">Skills</h3>
              <p className="text-sm text-body">Add your current skills and rate your proficiency:</p>
              <SkillSelector
                availableSkills={allSkills}
                selectedSkills={selectedSkills.map((s) => ({
                  skill: allSkills.find((as) => as.name === s.name) || { id: "", name: s.name, category: "" },
                  proficiency: s.proficiency,
                }))}
                onAdd={handleAddSkill}
                onRemove={(skillId) => {
                  const skill = allSkills.find((s) => s.id === skillId);
                  if (skill) handleRemoveSkill(skill.name);
                }}
                onUpdateProficiency={(skillId, proficiency) => {
                  const skill = allSkills.find((s) => s.id === skillId);
                  if (skill) handleUpdateProficiency(skill.name, proficiency);
                }}
              />
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back
        </Button>
        {step < steps.length - 1 ? (
          <Button onClick={() => setStep(step + 1)}>
            Next <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        ) : (
          <Button onClick={handleSubmit} disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save & Continue
          </Button>
        )}
      </div>
    </div>
  );
}
