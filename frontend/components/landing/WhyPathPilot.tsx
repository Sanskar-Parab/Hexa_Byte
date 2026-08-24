"use client";

import { Shield, Eye, Route, BarChart3 } from "lucide-react";

const reasons = [
  {
    icon: Shield,
    title: "Structured AI Guidance",
    description: "Not another chatbot. PathPilot provides structured, step-by-step career guidance with clear phases and milestones.",
    stat: "6-phase roadmap",
  },
  {
    icon: Eye,
    title: "Explainable Recommendations",
    description: "Every career match comes with a clear explanation of why it fits your profile. No black boxes.",
    stat: "100% transparent",
  },
  {
    icon: Route,
    title: "Personalized to You",
    description: "Roadmaps adapt to your pace, learning style, and goals. No generic advice — everything is tailored.",
    stat: "Custom plans",
  },
  {
    icon: BarChart3,
    title: "Track Real Progress",
    description: "See your skill growth over time with visual dashboards. Celebrate milestones and stay motivated.",
    stat: "Visual analytics",
  },
];

export function WhyPathPilot() {
  return (
    <section className="py-24 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <p className="text-sm font-semibold text-blue-600 tracking-wide uppercase">Why PathPilot</p>
            <h2 className="mt-2 text-3xl sm:text-4xl font-bold text-slate-900">
              Career guidance that actually works
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              Unlike generic career quizzes, PathPilot combines deep AI analysis with structured guidance to give you a clear, actionable plan.
            </p>

            <div className="mt-10 space-y-6">
              {reasons.map((reason) => {
                const Icon = reason.icon;
                return (
                  <div key={reason.title} className="flex gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50">
                      <Icon className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-slate-900">{reason.title}</h3>
                        <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                          {reason.stat}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-slate-600">{reason.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="relative">
            <div className="rounded-2xl border bg-gradient-to-br from-slate-900 to-slate-800 p-8 text-white shadow-2xl">
              <div className="flex items-center gap-2 mb-6">
                <div className="h-3 w-3 rounded-full bg-emerald-400" />
                <span className="text-sm text-slate-400">AI Analysis in Progress</span>
              </div>
              <div className="space-y-4">
                <div className="rounded-lg bg-white/10 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Skill Match Score</span>
                    <span className="text-emerald-400 font-bold">94%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-white/10">
                    <div className="h-2 rounded-full bg-gradient-to-r from-emerald-400 to-emerald-500" style={{ width: "94%" }} />
                  </div>
                </div>
                <div className="rounded-lg bg-white/10 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Interest Alignment</span>
                    <span className="text-blue-400 font-bold">87%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-white/10">
                    <div className="h-2 rounded-full bg-gradient-to-r from-blue-400 to-blue-500" style={{ width: "87%" }} />
                  </div>
                </div>
                <div className="rounded-lg bg-white/10 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Market Demand</span>
                    <span className="text-amber-400 font-bold">High</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-white/10">
                    <div className="h-2 rounded-full bg-gradient-to-r from-amber-400 to-amber-500" style={{ width: "80%" }} />
                  </div>
                </div>
              </div>
              <div className="mt-6 rounded-lg bg-emerald-500/20 border border-emerald-500/30 p-4">
                <p className="text-sm text-emerald-300 font-medium">
                  Recommendation: Data Scientist — Strong alignment with your Python and ML skills
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
