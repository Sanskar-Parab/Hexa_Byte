"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, LogOut, User, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/layout/Logo";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { getInitials } from "@/lib/utils";

const navLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/skills", label: "Skills" },
  { href: "/careers", label: "Careers" },
  { href: "/roadmap", label: "Roadmap" },
  { href: "/projects", label: "Projects" },
  { href: "/coach", label: "AI Coach" },
];

export function Header() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-hairline bg-canvas/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href={user ? "/dashboard" : "/"} className="shrink-0">
          <Logo />
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-full px-3.5 py-2 text-sm font-medium transition-colors",
                pathname === link.href || pathname.startsWith(link.href + "/")
                  ? "bg-canvas-soft2 text-ink"
                  : "text-body hover:text-ink hover:bg-canvas-soft"
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          {user ? (
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 rounded-full px-2 py-1.5 text-sm font-medium text-ink hover:bg-canvas-soft transition-colors"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-ink text-white text-xs font-semibold">
                  {getInitials(user.name)}
                </div>
                <span className="max-w-[120px] truncate">{user.name}</span>
                <ChevronDown className="h-4 w-4 text-mute" />
              </button>
              {dropdownOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setDropdownOpen(false)} />
                  <div className="absolute right-0 top-full z-50 mt-2 w-52 rounded-xl border border-hairline bg-canvas py-1 shadow-modal">
                    <div className="px-3 py-2.5 border-b border-hairline">
                      <p className="text-sm font-medium text-ink">{user.name}</p>
                      <p className="text-xs text-mute truncate">{user.email}</p>
                    </div>
                    <Link
                      href="/dashboard"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-body hover:bg-canvas-soft hover:text-ink"
                    >
                      <User className="h-4 w-4" />
                      Dashboard
                    </Link>
                    <button
                      onClick={() => { logout(); setDropdownOpen(false); }}
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm text-err hover:bg-err-soft"
                    >
                      <LogOut className="h-4 w-4" />
                      Sign out
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost" size="sm">Sign in</Button>
              </Link>
              <Link href="/register">
                <Button size="sm" className="rounded-full px-5">Get Started</Button>
              </Link>
            </>
          )}
        </div>

        <button className="md:hidden p-2 rounded-lg hover:bg-canvas-soft" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t border-hairline bg-canvas px-4 pb-4 pt-2">
          <nav className="flex flex-col gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  pathname === link.href
                    ? "bg-canvas-soft2 text-ink"
                    : "text-body hover:bg-canvas-soft"
                )}
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="mt-3 border-t border-hairline pt-3 flex flex-col gap-2">
            {user ? (
              <>
                <div className="flex items-center gap-2 px-3 py-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-ink text-white text-xs font-semibold">
                    {getInitials(user.name)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-ink">{user.name}</p>
                    <p className="text-xs text-mute">{user.email}</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={logout} className="justify-start text-err">
                  <LogOut className="mr-2 h-4 w-4" /> Sign out
                </Button>
              </>
            ) : (
              <>
                <Link href="/login" onClick={() => setMobileOpen(false)}>
                  <Button variant="outline" size="sm" className="w-full">Sign in</Button>
                </Link>
                <Link href="/register" onClick={() => setMobileOpen(false)}>
                  <Button size="sm" className="w-full rounded-full">Get Started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
