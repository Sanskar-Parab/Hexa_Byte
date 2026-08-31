import { CardSkeleton, SkeletonBlock } from "@/components/ui/loading-state";

function HeaderSkeleton() {
  return (
    <div className="mb-8 space-y-3">
      <SkeletonBlock className="h-3 w-28" />
      <SkeletonBlock className="h-7 w-64 max-w-full" />
      <SkeletonBlock className="h-4 w-96 max-w-full" />
    </div>
  );
}

type RouteLoadingVariant = "grid" | "list" | "chat" | "single" | "dashboard";

export function RouteLoading({ variant = "grid" }: { variant?: RouteLoadingVariant }) {
  return (
    <div className="mx-auto w-full max-w-5xl animate-fade-in">
      <HeaderSkeleton />

      {variant === "grid" && (
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      )}

      {variant === "list" && (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-xl border border-hairline bg-canvas p-4 shadow-card">
              <SkeletonBlock className="h-4 w-1/2" />
              <SkeletonBlock className="mt-2.5 h-3 w-1/3" />
            </div>
          ))}
        </div>
      )}

      {variant === "single" && <CardSkeleton />}

      {variant === "chat" && (
        <div className="flex h-[calc(100vh-320px)] min-h-[440px] flex-col justify-end gap-4 rounded-xl border border-hairline bg-canvas p-4 sm:p-6">
          <SkeletonBlock className="h-12 w-3/5 rounded-2xl" />
          <SkeletonBlock className="ml-auto h-10 w-2/5 rounded-2xl" />
          <SkeletonBlock className="h-14 w-4/5 rounded-2xl" />
        </div>
      )}

      {variant === "dashboard" && (
        <div className="space-y-6">
          <CardSkeleton />
          <div className="grid gap-6 md:grid-cols-2">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      )}
    </div>
  );
}
