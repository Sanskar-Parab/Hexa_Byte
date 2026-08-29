"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Rocket, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CardSkeleton } from "@/components/ui/loading-state";
import { api } from "@/lib/api";
import type { OpportunityRecommendation } from "@/types";

export function OpportunitiesForYou({ careerId }: { careerId?: string | null }) {
  const [items, setItems] = useState<OpportunityRecommendation[] | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .getOpportunityRecommendations({ type: "all", limit: 3, careerId: careerId || undefined })
      .then((data) => {
        if (cancelled) return;
        if (data.source_status === "unavailable") {
          setUnavailable(true);
          setItems([]);
        } else {
          setItems(data.recommendations);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setUnavailable(true);
          setItems([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [careerId]);

  if (items === null) {
    return <CardSkeleton />;
  }

  if (unavailable || items.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
          <Rocket className="h-4 w-4 text-mute" />
          Opportunities For You
        </CardTitle>
        <Link href="/opportunities" className="text-xs font-medium text-link hover:underline">
          View All &rarr;
        </Link>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.map((opp, i) => (
          <a
            key={`${opp.type}-${opp.id}`}
            href={opp.url || "/opportunities"}
            target={opp.url ? "_blank" : undefined}
            rel={opp.url ? "noopener noreferrer" : undefined}
            className="flex items-center justify-between gap-3 rounded-lg border border-hairline bg-canvas-soft p-3 transition-colors hover:bg-canvas-soft2"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-ink">
                {i === 0 && <span className="mr-1.5">🔥</span>}
                {opp.title}
              </p>
              <p className="truncate text-xs text-mute">{opp.organization}</p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Badge variant={opp.match_score >= 75 ? "success" : opp.match_score >= 50 ? "warning" : "outline"}>
                {opp.match_score}% Match
              </Badge>
              {opp.url && <ExternalLink className="h-3.5 w-3.5 text-mute" />}
            </div>
          </a>
        ))}
        <Link href="/opportunities" className="block pt-1">
          <Button variant="outline" size="sm" className="w-full">
            View All Opportunities
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
