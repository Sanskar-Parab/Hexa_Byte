"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert, LogOut } from "lucide-react";
import { Logo } from "@/components/layout/Logo";
import { Button } from "@/components/ui/button";
import { LoadingState } from "@/components/ui/loading-state";
import { useAuth } from "@/hooks/useAuth";

// This is NOT the student dashboard — a completely separate, admin-only
// analytics view for government/authority users. Gated on `is_admin`,
// which is never settable through any API (seeded/DB-set only).
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return <LoadingState fullScreen message="Loading admin workspace..." />;
  }

  if (!user) return null;

  if (!user.is_admin) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-canvas-soft px-6 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-err-soft">
          <ShieldAlert className="h-6 w-6 text-err-deep" />
        </div>
        <h1 className="text-xl font-semibold tracking-tight text-ink">Access restricted</h1>
        <p className="max-w-sm text-sm text-body">
          This is the government skilling-impact dashboard — a separate, administrator-only view.
          Your account doesn&apos;t have admin access.
        </p>
        <Button variant="outline" onClick={() => router.push("/dashboard")}>
          Back to your dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas-soft">
      <header className="sticky top-0 z-50 w-full border-b border-hairline bg-ink text-white">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Logo size="sm" className="[&_span:last-child]:text-white [&_span:last-child_span]:text-cyan" />
            <span className="hidden h-5 w-px bg-white/20 sm:block" />
            <span className="hidden text-sm font-medium text-white/80 sm:block">
              Skilling Impact Dashboard
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-white/60">{user.name}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => { logout(); router.push("/login"); }}
              className="text-white/80 hover:bg-white/10 hover:text-white"
            >
              <LogOut className="mr-1.5 h-3.5 w-3.5" /> Sign out
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
