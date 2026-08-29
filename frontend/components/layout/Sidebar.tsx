"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  Map,
  FolderKanban,
  MessageSquare,
  BarChart3,
  Settings,
  Compass,
  FileText,
  ClipboardCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/onboarding", label: "Profile Setup", icon: Settings },
  { href: "/assessment", label: "Assessment", icon: BarChart3 },
  { href: "/skills", label: "Skills", icon: Compass },
  { href: "/careers", label: "Careers", icon: Briefcase },
  { href: "/roadmap", label: "Roadmap", icon: Map },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/resume", label: "Resume", icon: FileText },
  { href: "/job-analyzer", label: "Job Match", icon: ClipboardCheck },
  { href: "/coach", label: "AI Coach", icon: MessageSquare },
];

export function Sidebar({ progress = 0 }: { progress?: number }) {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r border-hairline bg-canvas px-4 py-6">
      <nav className="flex flex-col gap-0.5 flex-1">
        {links.map((link) => {
          const Icon = link.icon;
          const active = pathname === link.href || pathname.startsWith(link.href + "/");
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-canvas-soft2 text-ink"
                  : "text-body hover:text-ink hover:bg-canvas-soft"
              )}
            >
              {active && <span className="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-full bg-ink" />}
              <Icon className={cn("h-[18px] w-[18px]", active ? "text-ink" : "text-mute")} />
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto pt-4 border-t border-hairline">
        <div className="rounded-xl bg-canvas-soft p-4">
          <p className="mb-2 text-xs font-medium text-body">Career Readiness</p>
          <Progress value={progress} className="h-1.5 bg-hairline" indicatorClassName="bg-ink" />
          <p className="mt-1.5 text-xs text-mute">{progress}% ready</p>
        </div>
      </div>
    </aside>
  );
}
