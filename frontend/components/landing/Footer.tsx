"use client";

import { Compass } from "lucide-react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-emerald-500">
              <Compass className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900">
              Path<span className="text-blue-600">Pilot</span>
            </span>
          </div>

          <nav className="flex items-center gap-6 text-sm text-slate-600">
            <Link href="/" className="hover:text-slate-900 transition-colors">Home</Link>
            <Link href="/careers" className="hover:text-slate-900 transition-colors">Careers</Link>
            <Link href="/login" className="hover:text-slate-900 transition-colors">Sign In</Link>
            <Link href="/register" className="hover:text-slate-900 transition-colors">Get Started</Link>
          </nav>

          <p className="text-sm text-slate-500">
            &copy; {new Date().getFullYear()} PathPilot AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
