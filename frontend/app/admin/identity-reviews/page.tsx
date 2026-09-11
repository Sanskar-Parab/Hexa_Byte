"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Clock, Check, X, ExternalLink, Eye } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SectionHeader } from "@/components/ui/section-header";
import { LoadingState } from "@/components/ui/loading-state";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { IdentityReview } from "@/types";

export default function IdentityReviewsPage() {
  const [reviews, setReviews] = useState<IdentityReview[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState<string>("pending");
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async (status?: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listIdentityReviews({ status: status || undefined, page: 1, page_size: 50 });
      setReviews(res.items);
      setTotal(res.total);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(filter);
  }, [filter]);

  const handleDecision = async (reviewId: string, decision: "link" | "reject") => {
    setActing(reviewId);
    setError(null);
    try {
      const res = await api.decideIdentityReview(reviewId, decision);
      // refresh
      await load(filter);
    } catch (e: any) {
      setError(e.message || "Decision failed");
    } finally {
      setActing(null);
    }
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Government — Identity Review"
        title="Medium-Confidence Matches"
        description="Review possible duplicates. Link records if same trainee, or mark as different person to create a new master. Phone is masked for privacy."
      />

      <div className="flex flex-wrap gap-2">
        {[
          { key: "pending", label: "Pending" },
          { key: "approved", label: "Approved" },
          { key: "rejected", label: "Rejected" },
          { key: "", label: "All" },
        ].map((f) => (
          <Button
            key={f.key || "all"}
            variant={filter === f.key ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </Button>
        ))}
        <div className="ml-auto flex items-center gap-2 text-xs text-mute">
          <span>{total} review{total !== 1 ? "s" : ""}</span>
          <Link href="/admin/trainees" className="text-link hover:underline"><Button variant="ghost" size="sm" className="h-7 text-xs">Back to Trainees</Button></Link>
        </div>
      </div>

      {loading ? (
        <LoadingState message="Loading reviews..." />
      ) : reviews.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Clock className="mx-auto h-10 w-10 text-mute/40" />
            <p className="mt-3 text-sm font-medium text-ink">No {filter || ""} reviews</p>
            <p className="mt-1 text-xs text-mute">
              {filter === "pending" ? "Medium-confidence matches will appear here for admin decision." : `No reviews with status "${filter}".`}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {error && <div className="rounded-md bg-err-soft p-3 text-sm text-err-deep">{error}</div>}
          {reviews.map((r) => (
            <Card key={r.id} className={r.status === "pending" ? "border-warn/40" : ""}>
              <CardHeader className="pb-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={r.status === "pending" ? "warning" : r.status === "approved" ? "success" : "destructive"}>
                      {r.status}
                    </Badge>
                    <span className="font-mono text-xs font-semibold text-ink">{r.match_score}%</span>
                    <Badge variant="secondary" className="text-[10px]">{r.confidence} confidence</Badge>
                    <span className="text-xs text-mute">{formatDate(r.created_at)}</span>
                  </div>
                  {r.status === "pending" ? (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleDecision(r.id, "link")}
                        disabled={!!acting}
                        className="h-8"
                      >
                        <Check className="mr-1 h-3.5 w-3.5" /> {acting === r.id ? "..." : "Link Records"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDecision(r.id, "reject")}
                        disabled={!!acting}
                        className="h-8"
                      >
                        <X className="mr-1 h-3.5 w-3.5" /> Not Same Person
                      </Button>
                    </div>
                  ) : (
                    <span className="text-xs text-mute">Decided {r.decided_at ? formatDate(r.decided_at) : ""}</span>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  {/* Incoming */}
                  <div className="rounded-lg border border-hairline bg-canvas-soft p-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-mute">New record (incoming)</p>
                    <div className="mt-2 space-y-1 text-sm">
                      <p><span className="text-mute">Name:</span> <span className="font-medium text-ink">{r.incoming_name}</span></p>
                      <p><span className="text-mute">DOB:</span> <span className="text-ink">{new Date(r.incoming_dob).toLocaleDateString("en-GB")}</span></p>
                      <p><span className="text-mute">Phone:</span> <span className="font-mono text-ink">{r.masked_phone || "—"}</span></p>
                      <p><span className="text-mute">Program:</span> <Badge variant="outline" className="ml-1">{r.incoming_program_name}</Badge> <span className="font-mono text-xs font-semibold text-ink">{r.incoming_program_trainee_id}</span></p>
                    </div>
                  </div>

                  {/* Matched */}
                  <div className="rounded-lg border border-hairline bg-link-soft/20 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-mute">Possible existing trainee</p>
                    {r.matched_master ? (
                      <div className="mt-2 space-y-1 text-sm">
                        <p><span className="text-mute">Master:</span> <span className="font-mono font-semibold text-ink">{r.matched_master.master_code}</span> — <span className="font-medium text-ink">{r.matched_master.primary_name}</span></p>
                        <p><span className="text-mute">DOB:</span> <span className="text-ink">{new Date(r.matched_master.dob).toLocaleDateString("en-GB")}</span></p>
                        <p><span className="text-mute">Phones:</span> <span className="font-mono text-xs text-ink">{r.matched_master.masked_phones.join(", ") || "—"}</span></p>
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {r.matched_master_enrollments.map((e) => (
                            <Badge key={e.id} variant="secondary" className="text-[11px]">
                              {e.program_name} / {e.program_trainee_id}
                            </Badge>
                          ))}
                        </div>
                        <Link href={`/admin/trainees/${r.matched_master.id}`} className="inline-flex items-center text-xs text-link hover:underline">
                          View master <ExternalLink className="ml-1 h-3 w-3" />
                        </Link>
                      </div>
                    ) : (
                      <p className="mt-2 text-sm text-mute">No matched master</p>
                    )}
                  </div>
                </div>

                {/* Field scores */}
                <div>
                  <p className="text-xs font-medium text-ink">Field comparison</p>
                  <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
                    <ScoreCell label="Name" value={r.field_scores.name} />
                    <ScoreCell label="DOB" value={r.field_scores.dob} />
                    <ScoreCell label="Phone" value={r.field_scores.phone} />
                    <ScoreCell label="Program" value={r.field_scores.program} />
                  </div>
                  <p className="mt-2 text-[11px] text-mute">
                    Program neutral (50%) when programs differ — IDs not comparable across programs. Phone mismatch = 0% but does not auto-reject (phones change).
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Card className="border-dashed">
        <CardContent className="py-3 text-xs text-mute">
          <p className="font-medium text-ink">Thresholds (MVP, tunable via env):</p>
          <p>85%+ high → auto-link · 60–84% medium → review · &lt;60% low → new master. High requires DOB exact + name ≥0.7 to avoid false merges.</p>
        </CardContent>
      </Card>
    </div>
  );
}

function ScoreCell({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const variant = value >= 0.9 ? "success" : value >= 0.5 ? "warning" : value === 0 ? "secondary" : "destructive";
  const badgeVariant = variant as any;
  return (
    <div className="rounded border border-hairline bg-canvas-soft2 px-2 py-2 text-center">
      <p className="text-[11px] font-medium uppercase tracking-wide text-mute">{label}</p>
      <p className="font-mono text-sm font-semibold text-ink">{pct}%</p>
      <Badge variant={badgeVariant} className="mt-1 text-[10px] px-1.5 py-0">{value === 1 ? "match" : value >= 0.9 ? "high" : value === 0 ? "mismatch" : `${pct}%`}</Badge>
    </div>
  );
}
