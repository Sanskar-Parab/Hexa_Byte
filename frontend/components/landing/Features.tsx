"use client";

import {
  Brain,
  BarChart3,
  Route,
  MessageSquare,
  TrendingUp,
  FolderKanban,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Career Intelligence",
    description: "AI analyzes your skills, interests, and market data to match you with ideal career paths.",
    color: "text-blue-600 bg-blue-50",
  },
  {
    icon: BarChart3,
    title: "Skill Gap Analysis",
    description: "Visualize exactly where you stand vs. where you need to be for your target career.",
    color: "text-emerald-600 bg-emerald-50",
  },
  {
    icon: Route,
    title: "Personalized Roadmap",
    description: "Get a step-by-step learning plan with phases, timelines, and hands-on activities.",
    color: "text-violet-600 bg-violet-50",
  },
  {
    icon: MessageSquare,
    title: "AI Career Coach",
    description: "Ask questions and get contextual advice about your career journey anytime.",
    color: "text-amber-600 bg-amber-50",
  },
  {
    icon: TrendingUp,
    title: "Progress Tracking",
    description: "Monitor your skill growth and career readiness with visual dashboards.",
    color: "text-rose-600 bg-rose-50",
  },
  {
    icon: FolderKanban,
    title: "Project Recommendations",
    description: "Build your portfolio with projects matched to your skill level and career goals.",
    color: "text-sky-600 bg-sky-50",
  },
];

export function Features() {
  return (
    <section className="py-24 bg-gradient-to-b from-slate-50 to-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-sm font-semibold text-blue-600 tracking-wide uppercase">Features</p>
          <h2 className="mt-2 text-3xl sm:text-4xl font-bold text-slate-900">
            Everything you need to navigate your career
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            From discovery to execution, PathPilot provides the tools and intelligence to make your next career move with confidence.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="rounded-2xl border bg-white p-6 shadow-sm hover:shadow-md transition-all duration-300 group"
              >
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${feature.color} mb-4 group-hover:scale-110 transition-transform`}>
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
