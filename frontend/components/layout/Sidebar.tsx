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
  { href: "/careers", label: "Career Matches", icon: Briefcase },
  { href: "/skills", label: "My Skills", icon: Compass },
  { href: "/roadmap", label: "Roadmap", icon: Map },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/resume", label: "Resume", icon: FileText },
  { href: "/job-analyzer", label: "Job Match", icon: ClipboardCheck },
  { href: "/coach", label: "AI Coach", icon: MessageSquare },
];

export function Sidebar({ progress = 0 }: { progress?: number }) {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-64 flex-col border-r bg-white px-4 py-6">
      <nav className="flex flex-col gap-1 flex-1">
        {links.map((link) => {
          const Icon = link.icon;
          const active = pathname === link.href || pathname.startsWith(link.href + "/");
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                active
                  ? "bg-blue-50 text-blue-700 shadow-sm"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              )}
            >
              <Icon className={cn("h-5 w-5", active ? "text-blue-600" : "text-slate-400")} />
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto pt-4 border-t">
        <div className="rounded-xl bg-gradient-to-br from-blue-50 to-emerald-50 p-4">
          <p className="text-xs font-medium text-slate-600 mb-2">Overall Progress</p>
          <Progress value={progress} className="h-2" />
          <p className="text-xs text-slate-500 mt-1.5">{progress}% complete</p>
        </div>
      </div>
    </aside>
  );
}
