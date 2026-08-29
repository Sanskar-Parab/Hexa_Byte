import { cn } from "@/lib/utils";

interface SectionHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
  titleClassName?: string;
}

export function SectionHeader({
  eyebrow,
  title,
  description,
  action,
  className,
  titleClassName,
}: SectionHeaderProps) {
  return (
    <div className={cn("flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div>
        {eyebrow && (
          <p className="mb-2 font-mono text-xs uppercase tracking-wider text-mute">{eyebrow}</p>
        )}
        <h2 className={cn("text-xl font-semibold tracking-tight text-ink sm:text-2xl", titleClassName)}>
          {title}
        </h2>
        {description && (
          <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-body">{description}</p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
