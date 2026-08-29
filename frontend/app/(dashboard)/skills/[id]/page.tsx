"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, MessageSquare, FolderKanban } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";
import { ConfidenceBadge } from "@/components/ui/status-badge";
import { EvidenceBadge } from "@/components/ui/evidence-badge";
import { SkillBar } from "@/components/ui/skill-bar";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { SkillEvidenceResponse } from "@/types";

export default function SkillDetailPage() {
  const params = useParams();
  const skillId = params?.id as string;
  const [data, setData] = useState<SkillEvidenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!skillId) return;
    api
      .getSkillEvidence(skillId)
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [skillId]);

  if (loading) {
    return <LoadingState message="Loading skill intelligence..." />;
  }

  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto">
        <EmptyState
          title="We couldn't load this skill"
          description="This skill may not exist, or you haven't added it to your profile yet."
          actionLabel="Back to Skills"
          actionHref="/skills"
        />
      </div>
    );
  }

  const sortedEvidence = [...(data.evidence || [])].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <Link href="/skills" className="inline-flex items-center gap-1.5 text-sm text-body hover:text-ink">
        <ArrowLeft className="h-4 w-4" />
        Back to Skills
      </Link>

      <SectionHeader
        eyebrow="Skill Intelligence"
        title={data.skill_name}
        description={data.level_name || "Not yet assessed"}
        action={<ConfidenceBadge confidence={data.confidence || "LOW"} />}
      />

      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-body">Current Proficiency</p>
            <p className="text-sm font-semibold text-ink">{data.proficiency}/5</p>
          </div>
          <SkillBar proficiency={data.proficiency} showLevelLabel />
        </CardContent>
      </Card>

      <div>
        <h3 className="text-sm font-mono uppercase tracking-wider text-mute mb-4">Evidence Timeline</h3>
        {sortedEvidence.length === 0 ? (
          <EmptyState
            title="No evidence yet"
            description="Take an AI assessment, complete a project, or upload a resume to start building evidence for this skill."
          />
        ) : (
          <div className="space-y-3">
            {sortedEvidence.map((ev) => (
              <Card key={ev.id}>
                <CardContent className="pt-5 flex items-start justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <EvidenceBadge sourceType={ev.source_type} />
                      <span className="text-xs text-mute">{formatDate(ev.created_at)}</span>
                    </div>
                    <p className="text-sm font-medium text-ink">{ev.title}</p>
                    {ev.description && <p className="text-sm text-body">{ev.description}</p>}
                    {ev.score !== null && ev.score !== undefined && (
                      <p className="text-xs text-mute">Score: {Math.round(ev.score)}%</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Card className="bg-canvas-soft2">
        <CardContent className="pt-6">
          <p className="text-xs font-mono uppercase tracking-wider text-mute mb-2">Next Action</p>
          <p className="text-sm text-ink mb-4">
            Build more evidence for {data.skill_name} with a hands-on project, or ask your AI coach how to close the gap fastest.
          </p>
          <div className="flex flex-wrap gap-2">
            <Link href="/projects">
              <Button size="sm">
                <FolderKanban className="h-4 w-4 mr-1.5" />
                Find a Project
              </Button>
            </Link>
            <Link href="/coach">
              <Button size="sm" variant="outline">
                <MessageSquare className="h-4 w-4 mr-1.5" />
                Ask AI Coach
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
