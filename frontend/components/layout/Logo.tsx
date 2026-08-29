import { cn } from "@/lib/utils";

export function Logo({ className, size = "md" }: { className?: string; size?: "sm" | "md" | "lg" }) {
  const box = size === "lg" ? "h-10 w-10" : size === "sm" ? "h-7 w-7" : "h-9 w-9";
  const text = size === "lg" ? "text-2xl" : size === "sm" ? "text-base" : "text-xl";

  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span className={cn("flex items-center justify-center rounded-lg bg-ink", box)}>
        <svg viewBox="0 0 32 32" fill="none" className="h-[55%] w-[55%]">
          <path d="M9 22.5L16 9.5L23 22.5" stroke="white" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="16" cy="16.5" r="2" fill="#50E3C2" />
        </svg>
      </span>
      <span className={cn("font-semibold tracking-tight text-ink", text)}>
        Next Path <span className="text-link">AI</span>
      </span>
    </span>
  );
}
