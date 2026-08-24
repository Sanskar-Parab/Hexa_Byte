"use client";

import { UserPlus, ClipboardCheck, Sparkles, BarChart3, Map, TrendingUp } from "lucide-react";

const steps = [
  {
    icon: UserPlus,
    title: "Create Your Profile",
    description: "Tell us about your education, experience, and career goals.",
    color: "from-blue-500 to-blue-600",
  },
  {
    icon: ClipboardCheck,
    title: "Take the Assessment",
    description: "Answer 20 questions about your interests, strengths, and work preferences.",
    color: "from-violet-500 to-violet-600",
  },
  {
    icon: Sparkles,
    title: "Get AI Recommendations",
    description: "Our AI analyzes your profile to suggest personalized career matches.",
    color: "from-emerald-500 to-emerald-600",
  },
  {
    icon: BarChart3,
    title: "View Skill Gaps",
    description: "See exactly which skills you need to develop for your target career.",
    color: "from-amber-500 to-amber-600",
  },
  {
    icon: Map,
    title: "Follow Your Roadmap",
    description: "Get a step-by-step learning plan tailored to your pace and goals.",
    color: "from-rose-500 to-rose-600",
  },
  {
    icon: TrendingUp,
    title: "Track Your Progress",
    description: "Monitor your growth and celebrate milestones along the way.",
    color: "from-sky-500 to-sky-600",
  },
];

export function HowItWorks() {
  return (
    <section className="py-24 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-sm font-semibold text-blue-600 tracking-wide uppercase">How It Works</p>
          <h2 className="mt-2 text-3xl sm:text-4xl font-bold text-slate-900">
            Your journey to the right career in 6 steps
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            PathPilot combines AI intelligence with structured guidance to help you make confident career decisions.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div
                key={step.title}
                className="relative group rounded-2xl border bg-white p-6 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
              >
                <div className="absolute -top-3 -left-3 flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-white text-sm font-bold shadow-lg">
                  {index + 1}
                </div>
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${step.color} mb-4`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{step.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{step.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
