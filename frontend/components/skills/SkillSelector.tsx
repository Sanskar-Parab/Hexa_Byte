"use client";

import { useState } from "react";
import { Search, Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Skill {
  id: string;
  name: string;
  category: string;
}

interface SelectedSkill {
  skill: Skill;
  proficiency: number;
}

interface SkillSelectorProps {
  availableSkills: Skill[];
  selectedSkills: SelectedSkill[];
  onAdd: (skillId: string, proficiency: number) => void;
  onRemove: (skillId: string) => void;
  onUpdateProficiency: (skillId: string, proficiency: number) => void;
}

export function SkillSelector({
  availableSkills,
  selectedSkills,
  onAdd,
  onRemove,
  onUpdateProficiency,
}: SkillSelectorProps) {
  const [search, setSearch] = useState("");
  const [newProficiency, setNewProficiency] = useState(3);
  const [addingSkill, setAddingSkill] = useState<string | null>(null);

  const selectedIds = new Set(selectedSkills.map((s) => s.skill.id));

  const filtered = availableSkills.filter(
    (skill) =>
      skill.name.toLowerCase().includes(search.toLowerCase()) &&
      !selectedIds.has(skill.id)
  );

  const grouped = filtered.reduce(
    (acc, skill) => {
      const category = skill.category || "Other";
      if (!acc[category]) acc[category] = [];
      acc[category].push(skill);
      return acc;
    },
    {} as Record<string, Skill[]>
  );

  const proficiencyLabels: Record<number, string> = {
    1: "Beginner",
    2: "Basic",
    3: "Intermediate",
    4: "Advanced",
    5: "Expert",
  };

  return (
    <div className="space-y-5">
      {selectedSkills.length > 0 && (
        <div>
          <p className="text-sm font-medium text-ink mb-2">Your Skills ({selectedSkills.length})</p>
          <div className="space-y-3">
            {selectedSkills.map((item) => (
              <div key={item.skill.id} className="flex items-center gap-3 rounded-lg border border-hairline p-3 bg-canvas">
                <div className="flex-1">
                  <p className="text-sm font-medium text-ink">{item.skill.name}</p>
                  <p className="text-xs text-mute">{item.skill.category}</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-32">
                    <Slider
                      value={[item.proficiency]}
                      min={1}
                      max={5}
                      step={1}
                      onValueCommit={([v]) => onUpdateProficiency(item.skill.id, v)}
                    />
                    <p className="text-xs text-mute text-center mt-1">
                      Level {item.proficiency} — {proficiencyLabels[item.proficiency]}
                    </p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => onRemove(item.skill.id)}>
                    <span className="text-err text-xs">Remove</span>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <p className="text-sm font-medium text-ink mb-2">Add Skills</p>
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-mute" />
          <Input
            placeholder="Search skills..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="max-h-64 overflow-y-auto space-y-3">
          {Object.entries(grouped).map(([category, skills]) => (
            <div key={category}>
              <p className="text-xs font-mono uppercase tracking-wider text-mute mb-1.5">
                {category}
              </p>
              <div className="flex flex-wrap gap-2">
                {skills.map((skill) => (
                  <button
                    key={skill.id}
                    disabled={addingSkill === skill.id}
                    onClick={() => {
                      setAddingSkill(skill.id);
                      onAdd(skill.id, newProficiency);
                      setTimeout(() => setAddingSkill(null), 500);
                    }}
                    className="inline-flex items-center gap-1.5 rounded-full border border-dashed border-hairline-strong bg-canvas-soft px-3 py-1.5 text-sm text-body hover:border-ink hover:bg-canvas-soft2 hover:text-ink transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    {skill.name}
                  </button>
                ))}
              </div>
            </div>
          ))}
          {Object.keys(grouped).length === 0 && (
            <p className="text-sm text-mute text-center py-4">
              {search ? "No skills found" : "All skills selected"}
            </p>
          )}
        </div>

        <div className="mt-3 pt-3 border-t border-hairline">
          <label className="text-xs text-mute">Default proficiency for new skills:</label>
          <div className="flex items-center gap-3 mt-1">
            <Slider
              value={[newProficiency]}
              min={1}
              max={5}
              step={1}
              onValueChange={([v]) => setNewProficiency(v)}
              className="w-32"
            />
            <span className="text-sm font-medium text-ink">Level {newProficiency} — {proficiencyLabels[newProficiency]}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
