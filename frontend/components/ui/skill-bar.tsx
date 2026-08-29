import { cn } from "@/lib/utils";

const LEVEL_LABELS = ["None", "Beginner", "Novice", "Intermediate", "Advanced", "Expert"];

interface SkillBarProps {
  proficiency: number;
  max?: number;
  showLevelLabel?: boolean;
  targetLevel?: number;
  className?: string;
}

export function SkillBar({ proficiency, max = 5, showLevelLabel, targetLevel, className }: SkillBarProps) {
  const segments = Array.from({ length: max });
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className="flex flex-1 gap-1">
        {segments.map((_, i) => {
          const filled = i < proficiency;
          const isTarget = targetLevel != null && i === targetLevel - 1 && targetLevel > proficiency;
          return (
            <div
              key={i}
              className={cn(
                "h-2 flex-1 rounded-full transition-colors",
                filled ? "bg-ink" : "bg-hairline",
                isTarget && !filled && "ring-2 ring-link/40"
              )}
            />
          );
        })}
      </div>
      {showLevelLabel && (
        <span className="w-20 shrink-0 text-right text-xs font-medium text-mute">
          {LEVEL_LABELS[proficiency] ?? proficiency}
        </span>
      )}
    </div>
  );
}
