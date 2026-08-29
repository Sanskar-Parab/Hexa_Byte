"use client";

import {
  Fingerprint,
  BarChart3,
  Route,
  MessageSquare,
  TrendingUp,
  FolderKanban,
} from "lucide-react";

const features = [
  {
    icon: Fingerprint,
    title: "Evidence-based skill profile",
    description: "Your proficiency is built from what you can demonstrate — assessments, projects, resume — each weighted by confidence.",
  },
  {
    icon: BarChart3,
    title: "Skill gap analysis",
    description: "See exactly where you stand against the skills your target career actually requires.",
  },
  {
    icon: Route,
    title: "Adaptive roadmap",
    description: "A phased plan that skips what you've already mastered and adjusts when your skills change.",
  },
  {
    icon: MessageSquare,
    title: "AI career coach",
    description: "Ask anything about your progress and get answers grounded in your real data — not generic advice.",
  },
  {
    icon: TrendingUp,
    title: "Career readiness tracking",
    description: "A single readiness score that moves as your evidence grows, so progress is never a guess.",
  },
  {
    icon: FolderKanban,
    title: "Projects that close gaps",
    description: "Every recommended project is selected to target your biggest current skill gap.",
  },
];

export function Features() {
  return (
    <section className="border-t border-hairline bg-canvas-soft py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto mb-16 max-w-xl text-center">
          <p className="mb-2 font-mono text-xs uppercase tracking-wider text-mute">Features</p>
          <h2 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            Everything you need to move with confidence.
          </h2>
          <p className="mt-4 text-base leading-relaxed text-body">
            From discovery to proof, Next Path AI gives you the intelligence to make your next
            career move deliberately.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="rounded-xl border border-hairline bg-canvas p-6 shadow-card transition-shadow hover:shadow-card-hover"
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-canvas-soft2">
                  <Icon className="h-5 w-5 text-ink" />
                </div>
                <h3 className="mb-1.5 text-base font-semibold text-ink">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-body">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
