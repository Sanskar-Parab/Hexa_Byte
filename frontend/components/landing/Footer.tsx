"use client";

import Link from "next/link";
import { Logo } from "@/components/layout/Logo";

export function Footer() {
  return (
    <footer className="border-t border-hairline bg-canvas">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
          <Logo size="sm" />

          <nav className="flex items-center gap-6 text-sm text-body">
            <Link href="/" className="transition-colors hover:text-ink">Home</Link>
            <Link href="/careers" className="transition-colors hover:text-ink">Careers</Link>
            <Link href="/login" className="transition-colors hover:text-ink">Sign in</Link>
            <Link href="/register" className="transition-colors hover:text-ink">Get started</Link>
          </nav>

          <p className="text-sm text-mute">
            &copy; {new Date().getFullYear()} Next Path AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
