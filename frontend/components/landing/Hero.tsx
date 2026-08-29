"use client";

import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

const LOOP = ["Assess", "Understand", "Match", "Identify gaps", "Learn", "Build", "Prove", "Adapt"];

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-canvas">
      <div className="mesh-gradient grid-overlay absolute inset-0" />
      <div className="absolute inset-x-0 top-0 h-px bg-hairline" />

      <div className="relative mx-auto max-w-6xl px-4 pb-20 pt-20 sm:px-6 sm:pt-28 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-hairline bg-canvas px-3 py-1 text-xs font-medium text-body shadow-card">
            <Sparkles className="h-3.5 w-3.5 text-link" />
            Evidence-based career intelligence
          </span>

          <h1 className="mx-auto mt-6 max-w-2xl text-[2.5rem] font-semibold leading-[1.1] tracking-tight text-ink sm:text-6xl">
            Know where you are.
            <br />
            Know where you&apos;re going.
            <br />
            Know what to do next.
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-body sm:text-lg">
            Next Path AI turns what you can actually demonstrate — assessments, projects, resume,
            real work — into a career match, a skill gap map, and an adaptive roadmap that updates
            as you grow.
          </p>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Link href="/register">
              <Button size="lg" className="rounded-full px-7">
                Start your assessment
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/careers">
              <Button size="lg" variant="outline" className="rounded-full px-7">
                Explore careers
              </Button>
            </Link>
          </div>
        </div>

        {/* Core product loop */}
        <div className="mx-auto mt-16 max-w-4xl">
          <div className="flex items-center justify-center gap-1.5 overflow-x-auto pb-2 sm:flex-wrap sm:justify-center">
            {LOOP.map((step, i) => (
              <div key={step} className="flex items-center gap-1.5 shrink-0">
                <span className="rounded-full border border-hairline bg-canvas px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider text-body">
                  {step}
                </span>
                {i < LOOP.length - 1 && <ArrowRight className="h-3 w-3 shrink-0 text-hairline-strong" />}
              </div>
            ))}
          </div>
        </div>

        {/* Product mock */}
        <div className="relative mx-auto mt-14 max-w-2xl">
          <div className="rounded-2xl border border-hairline bg-canvas p-6 shadow-panel">
            <div className="mb-5 flex items-center justify-between">
              <p className="font-mono text-xs uppercase tracking-wide text-mute">Career readiness</p>
              <span className="rounded-full bg-link-soft px-2.5 py-1 text-xs font-medium text-link-deep">
                Full Stack Developer
              </span>
            </div>
            <div className="flex items-end gap-3">
              <span className="text-5xl font-semibold tracking-tight text-ink">72%</span>
              <span className="mb-1.5 text-sm text-body">ready — 1 gap away from your next milestone</span>
            </div>
            <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-hairline">
              <div className="h-full w-[72%] rounded-full bg-ink" />
            </div>

            <div className="mt-6 space-y-3 border-t border-hairline pt-5">
              {[
                { skill: "JavaScript", level: 4 },
                { skill: "React", level: 3 },
                { skill: "Node.js", level: 2 },
              ].map((s) => (
                <div key={s.skill} className="flex items-center gap-4">
                  <span className="w-24 shrink-0 text-sm text-ink">{s.skill}</span>
                  <div className="flex flex-1 gap-1">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className={`h-2 flex-1 rounded-full ${i < s.level ? "bg-ink" : "bg-hairline"}`} />
                    ))}
                  </div>
                  <span className="w-10 shrink-0 text-right text-xs font-medium text-mute">{s.level}/5</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
