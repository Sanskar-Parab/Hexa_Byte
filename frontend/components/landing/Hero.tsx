"use client";

import Link from "next/link";
import { ArrowRight, Sparkles, TrendingUp, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-slate-50 via-white to-white">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
      <div className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] rounded-full bg-blue-100/40 blur-3xl" />
      <div className="absolute right-0 top-1/2 w-[600px] h-[400px] rounded-full bg-emerald-100/30 blur-3xl" />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 pb-24 sm:pt-28 sm:pb-32">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="animate-fade-in">
            <Badge variant="info" className="mb-6 px-3 py-1">
              <Sparkles className="mr-1.5 h-3.5 w-3.5" />
              AI-Powered Career Intelligence
            </Badge>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900 leading-[1.1]">
              Your Career Path,{" "}
              <span className="bg-gradient-to-r from-blue-600 to-emerald-500 bg-clip-text text-transparent">
                Personalized by AI
              </span>
            </h1>
            <p className="mt-6 text-lg text-slate-600 leading-relaxed max-w-lg">
              PathPilot analyzes your skills, interests, and goals to recommend the best career
              paths — with actionable roadmaps, skill gap analysis, and AI coaching to get you there.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link href="/register">
                <Button size="lg" className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-lg shadow-blue-500/25">
                  Start Career Assessment
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link href="/careers">
                <Button size="lg" variant="outline" className="border-slate-200">
                  Explore Careers
                </Button>
              </Link>
            </div>

            <div className="mt-10 flex items-center gap-8 text-sm text-slate-500">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-blue-500" />
                <span>50+ career paths</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-emerald-500" />
                <span>AI-powered matching</span>
              </div>
            </div>
          </div>

          <div className="relative animate-fade-in" style={{ animationDelay: "200ms" }}>
            <div className="relative rounded-2xl border bg-white p-6 shadow-2xl shadow-slate-200/50">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-3 w-3 rounded-full bg-rose-400" />
                <div className="h-3 w-3 rounded-full bg-amber-400" />
                <div className="h-3 w-3 rounded-full bg-emerald-400" />
                <span className="ml-2 text-xs text-slate-400 font-medium">Career Recommendations</span>
              </div>

              <div className="space-y-3">
                {[
                  { title: "Data Scientist", match: 94, color: "from-blue-500 to-blue-600" },
                  { title: "ML Engineer", match: 89, color: "from-emerald-500 to-emerald-600" },
                  { title: "Product Manager", match: 82, color: "from-violet-500 to-violet-600" },
                ].map((career, i) => (
                  <div
                    key={career.title}
                    className="flex items-center gap-4 rounded-xl border p-4 bg-slate-50/50 hover:bg-slate-50 transition-colors"
                    style={{ animationDelay: `${400 + i * 100}ms` }}
                  >
                    <div className={`flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br ${career.color} text-white text-sm font-bold`}>
                      {career.match}%
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-slate-900">{career.title}</p>
                      <div className="mt-1.5 h-2 w-full rounded-full bg-slate-200">
                        <div
                          className={`h-2 rounded-full bg-gradient-to-r ${career.color}`}
                          style={{ width: `${career.match}%` }}
                        />
                      </div>
                    </div>
                    <Badge variant="success" className="text-xs">High Match</Badge>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center gap-2 rounded-lg bg-emerald-50 p-3">
                <Sparkles className="h-4 w-4 text-emerald-600" />
                <p className="text-xs text-emerald-700 font-medium">
                  Based on your Python, ML, and analytics skills
                </p>
              </div>
            </div>

            <div className="absolute -bottom-4 -right-4 rounded-xl border bg-white p-3 shadow-lg">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100">
                  <TrendingUp className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-900">Skill Growth</p>
                  <p className="text-xs text-emerald-600 font-semibold">+23% this month</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
