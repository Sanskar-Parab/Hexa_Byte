import { type LucideIcon } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center rounded-xl border border-dashed border-hairline bg-canvas-soft px-6 py-16 text-center",
        className
      )}
    >
      {Icon && (
        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-canvas shadow-card">
          <Icon className="h-6 w-6 text-mute" />
        </div>
      )}
      <h3 className="text-lg font-semibold tracking-tight text-ink">{title}</h3>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-body">{description}</p>
      {actionLabel && (actionHref || onAction) && (
        <div className="mt-6">
          {actionHref ? (
            <Link href={actionHref}>
              <Button>{actionLabel}</Button>
            </Link>
          ) : (
            <Button onClick={onAction}>{actionLabel}</Button>
          )}
        </div>
      )}
    </div>
  );
}
