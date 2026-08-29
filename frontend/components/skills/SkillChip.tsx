"use client";

import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface SkillChipProps {
  name: string;
  proficiency?: number;
  onRemove?: () => void;
  className?: string;
}

export function SkillChip({ name, proficiency, onRemove, className }: SkillChipProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-hairline bg-canvas px-3 py-1.5 text-sm font-medium text-ink shadow-card",
        className
      )}
    >
      <span>{name}</span>
      {proficiency && (
        <div className="flex items-center gap-0.5">
          {[1, 2, 3, 4, 5].map((level) => (
            <div
              key={level}
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                level <= proficiency ? "bg-ink" : "bg-hairline"
              )}
            />
          ))}
        </div>
      )}
      {onRemove && (
        <button
          onClick={onRemove}
          className="ml-0.5 rounded-full p-0.5 hover:bg-canvas-soft2 transition-colors"
        >
          <X className="h-3 w-3 text-mute" />
        </button>
      )}
    </div>
  );
}
