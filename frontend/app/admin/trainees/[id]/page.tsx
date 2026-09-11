"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, GraduationCap, Shield, Calendar, Phone, Fingerprint, Building2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingState } from "@/components/ui/loading-state";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { MasterTraineeDetail } from "@/types";

export default function MasterDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [data, setData] = useState<MasterTraineeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api
      .getMasterDetail(id)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingState message="Loading master trainee..." />;
  if (error) return <Card><CardContent className="py-8 text-center text-sm text-err-deep">{error}</CardContent></Card>;
  if (!data) return <Card><CardContent className="py-8 text-center text-sm text-mute">Not found</CardContent></Card>;

  const { master, enrollments, longitudinal } = data;

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={() => router.push("/admin/trainees")} className="-ml-2">
        <ArrowLeft className="mr-1.5 h-4 w-4" /> Back to Trainee Identity
      </Button>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-ink">{master.master_code}</h1>
            <Badge variant="default" className="font-mono text-xs">{master.master_code}</Badge>
            <Badge variant="secondary">{enrollments.length} program{enrollments.length !== 1 ? "s" : ""}</Badge>
          </div>
          <p className="mt-1 text-lg font-medium text-ink">{master.primary_name}</p>
          <p className="text-sm text-mute">DOB {new Date(master.dob).toLocaleDateString("en-GB")} · Created {formatDate(master.created_at)}</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm"><Fingerprint className="h-4 w-4" /> Identity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-mute">Master ID</span><span className="font-mono font-medium text-ink">{master.master_code}</span></div>
            <div className="flex justify-between"><span className="text-mute">Name</span><span className="font-medium text-ink">{master.primary_name}</span></div>
            <div className="flex justify-between"><span className="text-mute flex items-center gap-1"><Calendar className="h-3 w-3" /> DOB</span><span className="text-ink">{new Date(master.dob).toLocaleDateString("en-GB")}</span></div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm"><Phone className="h-4 w-4" /> Phones</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {master.phone_numbers.length === 0 && <span className="text-sm text-mute">No phone</span>}
              {master.phone_numbers.map((p, i) => (
                <div key={i} className="rounded-md border border-hairline bg-canvas-soft2 px-2.5 py-1.5 text-xs">
                  <p className="font-mono text-ink">{p}</p>
                  <p className="text-[11px] text-mute">masked: {master.masked_phones[i]}</p>
                </div>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-mute">All phone numbers observed for this trainee — phone change does not create a new master.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm"><Building2 className="h-4 w-4" /> Longitudinal</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            {longitudinal?.linked_user_id ? (
              <div className="space-y-1">
                <p><span className="text-mute">Linked User:</span> <span className="font-mono text-xs text-ink">{longitudinal.linked_user_id.slice(0, 8)}…</span></p>
                <p><span className="text-mute">Enrollments:</span> <span className="font-medium text-ink">{longitudinal.enrollment_count}</span></p>
                <p><span className="text-mute">Outcomes:</span> <span className="font-medium text-ink">{longitudinal.outcome_count}</span></p>
              </div>
            ) : (
              <p className="text-mute">No linked user account yet. This master tracks program history independently; link to a User to surface training &amp; placement timeline.</p>
            )}
            <p className="mt-2 text-[11px] text-mute">Future: Master → Program History → Skills → Career Path → Placement</p>
          </CardContent>
        </Card>
      </div>

      {/* Program enrollments */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base"><GraduationCap className="h-4 w-4" /> Program History — all program-specific IDs retained</CardTitle>
        </CardHeader>
        <CardContent>
          {enrollments.length === 0 ? (
            <p className="py-6 text-center text-sm text-mute">No program records</p>
          ) : (
            <div className="space-y-3">
              {/* Visual tree */}
              <div className="rounded-lg border border-hairline bg-canvas-soft/50 p-4">
                <p className="font-mono text-sm font-semibold text-ink">{master.master_code} — {master.primary_name}</p>
                <div className="mt-3 space-y-2">
                  {enrollments.map((e) => (
                    <div key={e.id} className="flex items-center gap-3 text-sm">
                      <span className="text-mute">├─</span>
                      <Badge variant="outline" className="font-mono text-xs">{e.program_name}</Badge>
                      <span className="font-mono text-xs font-semibold text-ink">{e.program_trainee_id}</span>
                      <span className="text-body">{e.trainee_name}</span>
                      <span className="text-xs text-mute">{new Date(e.dob).toLocaleDateString("en-GB")}</span>
                      <Badge variant="secondary" className="text-[11px]">{e.masked_phone || "no phone"}</Badge>
                      <span className="ml-auto text-xs text-mute">{formatDate(e.created_at)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] text-sm">
                  <thead>
                    <tr className="border-b border-hairline text-left text-xs font-medium uppercase tracking-wide text-mute">
                      <th className="py-2 pr-4">Program</th>
                      <th className="py-2 pr-4">Program Trainee ID</th>
                      <th className="py-2 pr-4">Name on Record</th>
                      <th className="py-2 pr-4">DOB</th>
                      <th className="py-2 pr-4">Phone (masked)</th>
                      <th className="py-2 pr-4">Added</th>
                    </tr>
                  </thead>
                  <tbody>
                    {enrollments.map((e) => (
                      <tr key={e.id} className="border-b border-hairline last:border-0">
                        <td className="py-3 pr-4"><Badge variant="outline">{e.program_name}</Badge></td>
                        <td className="py-3 pr-4 font-mono text-xs font-semibold text-ink">{e.program_trainee_id}</td>
                        <td className="py-3 pr-4 text-ink">{e.trainee_name}</td>
                        <td className="py-3 pr-4 text-body">{new Date(e.dob).toLocaleDateString("en-GB")}</td>
                        <td className="py-3 pr-4 text-xs text-body">{e.masked_phone || "—"}</td>
                        <td className="py-3 pr-4 text-xs text-mute">{formatDate(e.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-mute">Original program IDs are <span className="font-semibold text-ink">never overwritten</span> — this is the audit trail.</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-dashed">
        <CardContent className="py-4 text-xs text-mute">
          <p className="font-medium text-ink">Explainable linking</p>
          <p className="mt-1">Each program record was added via admin → Run Identity Matching → weighted score (Name 30%, DOB 30%, Phone 15%, Program 25%). High (85%+) auto-linked, medium flagged for review, low creates new master. DOB mismatch or name &lt;0.7 caps high to medium to avoid false merges.</p>
        </CardContent>
      </Card>
    </div>
  );
}
