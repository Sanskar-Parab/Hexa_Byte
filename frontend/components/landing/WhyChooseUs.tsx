"use client";

import { ShieldCheck, Eye, Route, LineChart } from "lucide-react";

const reasons = [
  {
    icon: ShieldCheck,
    title: "Not another quiz",
    description: "Next Path AI builds a structured, multi-phase plan with clear milestones — not a one-off personality result.",
    stat: "8-stage loop",
  },
  {
    icon: Eye,
    title: "Explainable, always",
    description: "Every match, gap, and recommendation comes with the reasoning behind it. No black boxes.",
    stat: "Fully transparent",
  },
  {
    icon: Route,
    title: "Adapts as you grow",
    description: "When your proficiency changes, your roadmap changes with it — content you've outgrown gets skipped automatically.",
    stat: "Adaptive by design",
  },
  {
    icon: LineChart,
    title: "Grounded in evidence",
    description: "Confidence is scored by source — an AI assessment and a shipped project count more than a self-rating.",
    stat: "Evidence-weighted",
  },
];

export function WhyChooseUs() {
  return (
    <section className="border-t border-hairline bg-canvas py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-16 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="mb-2 font-mono text-xs uppercase tracking-wider text-mute">Why Next Path AI</p>
            <h2 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
              Career guidance built on proof, not vibes.
            </h2>
            <p className="mt-4 text-base leading-relaxed text-body">
              Generic quizzes guess. Next Path AI measures — then tells you exactly what to do
              about it.
            </p>

            <div className="mt-10 space-y-6">
              {reasons.map((reason) => {
                const Icon = reason.icon;
                return (
                  <div key={reason.title} className="flex gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-canvas-soft2">
                      <Icon className="h-5 w-5 text-ink" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold text-ink">{reason.title}</h3>
                        <span className="rounded-full bg-link-soft px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide text-link-deep">
                          {reason.stat}
                        </span>
                      </div>
                      <p className="mt-1 text-sm leading-relaxed text-body">{reason.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="relative">
            <div className="rounded-2xl border border-hairline bg-ink p-8 text-white shadow-panel">
              <div className="mb-6 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-cyan" />
                <span className="font-mono text-xs uppercase tracking-wide text-white/50">
                  Analysis in progress
                </span>
              </div>
              <div className="space-y-4">
                <div className="rounded-lg bg-white/5 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium">Skill match score</span>
                    <span className="font-semibold text-cyan">94%</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-white/10">
                    <div className="h-full w-[94%] rounded-full bg-cyan" />
                  </div>
                </div>
                <div className="rounded-lg bg-white/5 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium">Evidence confidence</span>
                    <span className="font-semibold text-white">High</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-white/10">
                    <div className="h-full w-[87%] rounded-full bg-white" />
                  </div>
                </div>
                <div className="rounded-lg bg-white/5 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium">Market demand</span>
                    <span className="font-semibold text-warn">High</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-white/10">
                    <div className="h-full w-[80%] rounded-full bg-warn" />
                  </div>
                </div>
              </div>
              <div className="mt-6 rounded-lg border border-white/10 bg-white/5 p-4">
                <p className="text-sm text-white/80">
                  Recommendation: <span className="font-medium text-white">Data Scientist</span> —
                  strong alignment with your Python and analytics evidence.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
