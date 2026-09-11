"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, Check, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { EmploymentOutcome } from "@/types";

function evidenceLabel(level?: string | null, verified?: boolean): string {
  const lvl = (level || (verified ? "verified" : "self_reported")).toLowerCase();
  if (lvl === "verified") return "✓ Verified";
  if (lvl === "evidence_submitted") return "Evidence submitted";
  return "Self-reported";
}

function evidenceVariant(level?: string | null, verified?: boolean): "default" | "secondary" | "success" | "outline" | "warning" {
  const lvl = (level || (verified ? "verified" : "self_reported")).toLowerCase();
  if (lvl === "verified") return "success";
  if (lvl === "evidence_submitted") return "warning";
  return "outline";
}

export function VerificationQueue() {
  const [outcomes, setOutcomes] = useState<EmploymentOutcome[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAdminEmploymentOutcomes({ limit: 50 });
      setOutcomes(data);
    } catch (err: any) {
      setError(err.message || "Failed to load outcomes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleVerify = async (id: string) => {
    setVerifyingId(id);
    setError(null);
    try {
      await api.verifyOutcome(id);
      await load();
    } catch (err: any) {
      setError(err.message || "Verification failed");
    } finally {
      setVerifyingId(null);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center gap-2 p-6 text-sm text-body">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading verification queue...
        </CardContent>
      </Card>
    );
  }

  if (outcomes.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
            <ShieldCheck className="h-4 w-4 text-mute" /> Employer Verification
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-mute">No employment outcomes to verify yet.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
          <ShieldCheck className="h-4 w-4 text-mute" /> Employer Verification (Admin-only)
        </CardTitle>
        <p className="mt-1 text-xs text-mute">
          Honest labeling: this is admin verification, not an external employer login. Verifying sets{" "}
          <code className="rounded bg-canvas-soft2 px-1 py-0.5">verified=true</code>,{" "}
          <code className="rounded bg-canvas-soft2 px-1 py-0.5">source=verified_employer</code>,{" "}
          <code className="rounded bg-canvas-soft2 px-1 py-0.5">evidence_level=verified</code>.
        </p>
      </CardHeader>
      <CardContent>
        {error && <p className="mb-3 text-sm text-err-deep">{error}</p>}
        <div className="space-y-2">
          {outcomes.map((o) => {
            const isVerified = (o as any).evidence_level === "verified" || o.verified;
            const level = (o as any).evidence_level || (o.verified ? "verified" : "self_reported");
            return (
              <div key={o.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-hairline p-3">
                <div className="min-w-0 space-y-1">
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <span className="font-medium capitalize text-ink">{o.employment_status.replace("_", " ")}</span>
                    {o.job_title && <span className="text-body">{o.job_title}</span>}
                    {o.company_name && <span className="text-mute">at {o.company_name}</span>}
                    <Badge variant={evidenceVariant(level, o.verified) as any} className="text-[10px]">
                      {evidenceLabel(level, o.verified)}
                    </Badge>
                    {o.source && <span className="text-xs text-mute">· {o.source}</span>}
                  </div>
                  <div className="text-xs text-mute">
                    {o.location || "Location not shared"} · {o.employment_type || "type not shared"}
                  </div>
                </div>
                <div className="shrink-0">
                  {isVerified ? (
                    <span className="inline-flex items-center gap-1 text-sm font-medium text-link">
                      <Check className="h-4 w-4" /> Verified
                    </span>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleVerify(o.id)}
                      disabled={!!verifyingId}
                    >
                      {verifyingId === o.id ? (
                        <>
                          <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> Verifying...
                        </>
                      ) : (
                        "Verify Outcome"
                      )}
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
