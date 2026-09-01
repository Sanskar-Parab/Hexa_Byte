"use client";

import Link from "next/link";
import {
  MapPin,
  Briefcase,
  Wallet,
  CalendarClock,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Map as MapIcon,
  FolderKanban,
  Globe,
  Gauge,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { OpportunityRecommendation } from "@/types";

function scoreTone(score: number) {
  if (score >= 75) return { text: "text-link-deep", ring: "border-link/30 bg-link-soft/40" };
  if (score >= 50) return { text: "text-warn-deep", ring: "border-warn/30 bg-warn-soft/40" };
  return { text: "text-err-deep", ring: "border-err/30 bg-err-soft/40" };
}

export function OpportunityCard({ opportunity }: { opportunity: OpportunityRecommendation }) {
  const {
    title,
    organization,
    organization_url,
    type,
    url,
    logo,
    location,
    remote,
    work_type,
    seniority,
    salary,
    posted_date,
    valid_through,
    source,
    match_score,
    matched_skills,
    partial_skills,
    missing_skills,
    why_match,
    skill_gap_message,
    recommendation,
  } = opportunity;

  const tone = scoreTone(match_score);

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-5 sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-canvas-soft2 text-sm font-semibold text-mute">
              {logo ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={logo} alt="" className="h-full w-full object-cover" />
              ) : (
                organization.slice(0, 1).toUpperCase()
              )}
            </div>
            <div className="min-w-0">
              <p className="truncate text-base font-semibold text-ink">{title}</p>
              {organization_url ? (
                <a
                  href={organization_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="truncate text-sm text-body hover:text-link hover:underline"
                >
                  {organization}
                </a>
              ) : (
                <p className="truncate text-sm text-body">{organization}</p>
              )}
              <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-mute">
                <Badge variant="secondary" className="capitalize">{type}</Badge>
                {location && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3 w-3" /> {location}
                  </span>
                )}
                {remote === true && (
                  <span className="inline-flex items-center gap-1">
                    <Globe className="h-3 w-3" /> Remote
                  </span>
                )}
                {remote === false && (
                  <span className="inline-flex items-center gap-1">
                    <Globe className="h-3 w-3" /> On-site
                  </span>
                )}
                {work_type && (
                  <span className="inline-flex items-center gap-1">
                    <Briefcase className="h-3 w-3" /> {work_type}
                  </span>
                )}
                {seniority && (
                  <span className="inline-flex items-center gap-1">
                    <Gauge className="h-3 w-3" /> {seniority}
                  </span>
                )}
                {salary && (
                  <span className="inline-flex items-center gap-1">
                    <Wallet className="h-3 w-3" /> {salary}
                  </span>
                )}
                {posted_date && (
                  <span className="inline-flex items-center gap-1">
                    <CalendarClock className="h-3 w-3" /> Posted {new Date(posted_date).toLocaleDateString()}
                  </span>
                )}
                {!posted_date && valid_through && (
                  <span className="inline-flex items-center gap-1">
                    <CalendarClock className="h-3 w-3" /> Closes {new Date(valid_through).toLocaleDateString()}
                  </span>
                )}
                {source && <span className="text-hairline-strong">via {source}</span>}
              </div>
            </div>
          </div>

          <div className={cn("flex shrink-0 flex-col items-center rounded-xl border px-3 py-2", tone.ring)}>
            <span className={cn("text-xl font-semibold leading-none", tone.text)}>{match_score}%</span>
            <span className="mt-0.5 text-[10px] uppercase tracking-wide text-mute">Match</span>
          </div>
        </div>

        {why_match.length > 0 && (
          <div className="mt-4">
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-mute">Why you're a good fit</p>
            <ul className="space-y-1">
              {why_match.slice(0, 3).map((reason, i) => (
                <li key={i} className="flex items-start gap-1.5 text-sm text-body">
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-link" />
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        )}

        {recommendation && (
          <p className="mt-3 rounded-lg bg-canvas-soft px-3 py-2 text-sm text-body">{recommendation}</p>
        )}

        {(matched_skills.length > 0 || partial_skills.length > 0) && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {matched_skills.map((s) => (
              <Badge key={s.skill} variant="success">✓ {s.skill}</Badge>
            ))}
            {partial_skills.map((s) => (
              <Badge key={s.skill} variant="warning">△ {s.skill}</Badge>
            ))}
          </div>
        )}

        {missing_skills.length > 0 && (
          <div className="mt-4 rounded-lg border border-hairline bg-canvas-soft p-3">
            <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-mute">
              <AlertTriangle className="h-3.5 w-3.5 text-warn-deep" />
              Skills to improve
            </p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {missing_skills.map((skill) => (
                <Badge key={skill} variant="outline">{skill}</Badge>
              ))}
            </div>
            {skill_gap_message && <p className="mt-2 text-xs text-mute">{skill_gap_message}</p>}
            <div className="mt-3 flex flex-wrap gap-2">
              <Link href="/roadmap">
                <Button variant="outline" size="sm" className="text-xs">
                  <MapIcon className="mr-1.5 h-3.5 w-3.5" /> Add to Roadmap
                </Button>
              </Link>
              <Link href="/projects">
                <Button variant="outline" size="sm" className="text-xs">
                  <FolderKanban className="mr-1.5 h-3.5 w-3.5" /> Find a Project
                </Button>
              </Link>
            </div>
          </div>
        )}

        <div className="mt-4">
          {url ? (
            <a href={url} target="_blank" rel="noopener noreferrer">
              <Button className="w-full sm:w-auto">
                Apply Now <ExternalLink className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            </a>
          ) : (
            <Button className="w-full sm:w-auto" disabled>
              Link unavailable
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
