import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  message?: string;
  fullScreen?: boolean;
  className?: string;
}

export function LoadingState({ message = "Loading...", fullScreen, className }: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 py-24 text-center",
        fullScreen && "min-h-screen",
        className
      )}
    >
      <Loader2 className="h-6 w-6 animate-spin text-ink" />
      <p className="text-sm text-body">{message}</p>
    </div>
  );
}

export function SkeletonBlock({ className }: { className?: string }) {
  return <div className={cn("skeleton rounded-lg", className)} />;
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-hairline bg-canvas p-6 shadow-card">
      <SkeletonBlock className="h-4 w-1/3" />
      <SkeletonBlock className="mt-4 h-3 w-full" />
      <SkeletonBlock className="mt-2 h-3 w-2/3" />
      <SkeletonBlock className="mt-5 h-2 w-full" />
    </div>
  );
}
