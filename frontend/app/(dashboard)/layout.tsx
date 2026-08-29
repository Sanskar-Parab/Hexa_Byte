"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { LoadingState } from "@/components/ui/loading-state";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      api.getDashboard().then((data) => setProgress(data.overall_progress || 0)).catch(() => {});
    }
  }, [user]);

  if (loading) {
    return <LoadingState fullScreen message="Loading your workspace..." />;
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-canvas-soft">
      <Header />
      <div className="flex">
        <Sidebar progress={progress} />
        <main className="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 overflow-x-hidden">{children}</main>
      </div>
    </div>
  );
}
