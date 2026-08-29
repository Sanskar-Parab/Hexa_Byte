import { Brain, FolderKanban, FileText, Briefcase, User, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";

const SOURCE_CONFIG: Record<string, { label: string; icon: typeof User }> = {
  assessment: { label: "AI Assessment", icon: Brain },
  project: { label: "Project", icon: FolderKanban },
  resume: { label: "Resume", icon: FileText },
  job: { label: "Job Match", icon: Briefcase },
  practical: { label: "Practical Task", icon: Wrench },
  manual: { label: "Self-Reported", icon: User },
};

export function EvidenceBadge({ sourceType, className }: { sourceType: string; className?: string }) {
  const config = SOURCE_CONFIG[sourceType] ?? SOURCE_CONFIG.manual;
  const Icon = config.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-hairline bg-canvas px-2.5 py-1 text-xs font-medium text-body",
        className
      )}
    >
      <Icon className="h-3.5 w-3.5 text-ink" />
      {config.label}
    </span>
  );
}
