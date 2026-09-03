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
  switch (confidence?.toLowerCase()) {
    case "high":
      return "text-link bg-link-soft";
    case "medium":
      return "text-warn-deep bg-warn-soft";
    case "low":
      return "text-err-deep bg-err-soft";
    default:
      return "text-body bg-canvas-soft2";
  }
}

export function getDifficultyColor(difficulty: string): string {
  switch (difficulty?.toUpperCase()) {
    case "BEGINNER":
      return "bg-link-soft text-link-deep";
    case "INTERMEDIATE":
      return "bg-warn-soft text-warn-deep";
    case "ADVANCED":
      return "bg-err-soft text-err-deep";
    case "INDUSTRY":
      return "bg-violet-soft text-violet-deep";
    default:
      return "bg-canvas-soft2 text-body";
  }
}

export function getStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case "completed":
      return "text-link bg-link-soft";
    case "in_progress":
      return "text-warn-deep bg-warn-soft";
    case "not_started":
    default:
      return "text-mute bg-canvas-soft2";
  }
}

export function formatCurrency(amount: number, currency?: string | null): string {
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: currency || "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${currency || ""} ${amount.toLocaleString("en-IN")}`.trim();
  }
}

export function formatPercent(value: number | null | undefined): string {
  return value === null || value === undefined ? "No data" : `${value}%`;
}

export function formatStatusLabel(status: string): string {
  switch (status?.toLowerCase()) {
    case "completed":
      return "Completed";
    case "in_progress":
      return "In Progress";
    case "not_started":
      return "Not Started";
    default:
      return status;
  }
}
