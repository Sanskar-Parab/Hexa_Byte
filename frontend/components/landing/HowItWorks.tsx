"use client";

import { UserPlus, ClipboardCheck, Target, BarChart3, Map, Hammer } from "lucide-react";

const steps = [
  {
    icon: UserPlus,
    title: "Tell us about you",
    description: "Share your background, experience, and interests in a short guided setup.",
  },
  {
    icon: ClipboardCheck,
    title: "Assess your skills",
    description: "An adaptive assessment measures what you actually know — not just what you claim.",
  },
  {
    icon: Target,
    title: "Match to careers",
    description: "See which careers fit your demonstrated skills, ranked by match score and confidence.",
  },
  {
    icon: BarChart3,
    title: "Identify your gaps",
    description: "A clear breakdown of exactly which skills stand between you and your target role.",
  },
  {
    icon: Map,
    title: "Follow an adaptive roadmap",
    description: "A phased learning path that adjusts automatically as your proficiency changes.",
  },
  {
    icon: Hammer,
    title: "Build and prove it",
    description: "Ship matched projects that generate real evidence — not just self-reported claims.",
  },
];

export function HowItWorks() {
  return (
    <section className="border-t border-hairline bg-canvas py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto mb-16 max-w-xl text-center">
          <p className="mb-2 font-mono text-xs uppercase tracking-wider text-mute">How it works</p>
          <h2 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            One loop, repeated until you&apos;re ready.
          </h2>
          <p className="mt-4 text-base leading-relaxed text-body">
            Next Path AI runs the same intelligence loop behind every recommendation: assess,
            understand, match, close gaps, and adapt.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div
                key={step.title}
                className="group rounded-xl border border-hairline bg-canvas p-6 shadow-card transition-shadow hover:shadow-card-hover"
              >
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-canvas-soft2">
                    <Icon className="h-5 w-5 text-ink" />
                  </div>
                  <span className="font-mono text-xs text-hairline-strong">0{index + 1}</span>
                </div>
                <h3 className="mb-1.5 text-base font-semibold text-ink">{step.title}</h3>
                <p className="text-sm leading-relaxed text-body">{step.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
