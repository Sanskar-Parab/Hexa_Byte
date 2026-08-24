import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function getConfidenceColor(confidence: string): string {
  switch (confidence) {
    case "high":
      return "text-emerald-600 bg-emerald-50";
    case "medium":
      return "text-amber-600 bg-amber-50";
    case "low":
      return "text-rose-600 bg-rose-50";
    default:
      return "text-slate-600 bg-slate-50";
  }
}

export function getDifficultyColor(difficulty: string): string {
  switch (difficulty) {
    case "beginner":
      return "bg-emerald-100 text-emerald-700";
    case "intermediate":
      return "bg-amber-100 text-amber-700";
    case "advanced":
      return "bg-rose-100 text-rose-700";
    default:
      return "bg-slate-100 text-slate-700";
  }
}
