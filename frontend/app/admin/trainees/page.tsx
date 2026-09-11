"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Plus, Users, Eye, CheckCircle, Clock, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { SectionHeader } from "@/components/ui/section-header";
import { LoadingState } from "@/components/ui/loading-state";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { MasterTrainee, CreateTraineeResponse, IdentityReview } from "@/types";

export default function TraineesPage() {
  const [masters, setMasters] = useState<MasterTrainee[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);

  // Add form state
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({
    trainee_name: "",
    dob: "",
    phone: "",
    program_name: "PMKVY",
    program_trainee_id: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<CreateTraineeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async (searchVal?: string) => {
    setLoading(true);
    try {
      const res = await api.listMasters({ page: 1, page_size: 50, search: searchVal || undefined });
      setMasters(res.items);
      setTotal(res.total);
      // pending reviews count
      const reviews = await api.listIdentityReviews({ status: "pending", page: 1, page_size: 1 });
      setPendingCount(reviews.total);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load(search);
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      // Basic validation
      if (!form.trainee_name || !form.dob || !form.program_name || !form.program_trainee_id) {
        throw new Error("Please fill name, DOB, program and program trainee ID");
      }
      // dob is YYYY-MM-DD from input, backend expects ISO date
      const res = await api.createTraineeRecord({
        trainee_name: form.trainee_name.trim(),
        dob: form.dob,
        phone: form.phone.trim() || undefined,
        program_name: form.program_name.trim(),
        program_trainee_id: form.program_trainee_id.trim(),
      });
      setResult(res);
      // refresh list
      await load(search);
    } catch (e: any) {
      setError(e.message || "Failed to create");
    } finally {
      setSubmitting(false);
    }
  };

  const closeAdd = () => {
    setShowAdd(false);
    setResult(null);
    setError(null);
    setForm({ trainee_name: "", dob: "", phone: "", program_name: "PMKVY", program_trainee_id: "" });
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Government — Trainee Identity Resolution"
        title="Master Trainee Identity"
        description="Link the same real-world trainee across different programs. Each program retains its own ID; the Master Trainee (MT-xxxxx) is the persistent identity. Deterministic weighted matching explains every link."
      />

      {/* Stats */}
      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-link-soft">
                <Users className="h-5 w-5 text-link" />
              </div>
              <div>
                <p className="text-2xl font-semibold text-ink">{total}</p>
                <p className="text-xs text-mute">Master Trainees</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-warn-soft">
                <Clock className="h-5 w-5 text-warn-deep" />
              </div>
              <div>
                <p className="text-2xl font-semibold text-ink">{pendingCount}</p>
                <p className="text-xs text-mute">Pending Reviews</p>
              </div>
            </div>
            {pendingCount > 0 && (
              <Link href="/admin/identity-reviews" className="mt-2 inline-flex text-xs text-link hover:underline">
                View reviews <ExternalLink className="ml-1 h-3 w-3" />
              </Link>
            )}
          </CardContent>
        </Card>
        <Card className="bg-ink text-white">
          <CardContent className="pt-6">
            <p className="text-xs font-medium uppercase tracking-wide text-white/60">How it works</p>
            <p className="mt-1 text-sm text-white/80">
              Name 30% · DOB 30% · Phone 15% · Program 25% → <span className="font-semibold text-white">85%+ auto-link, 60-84% review, &lt;60% new</span>
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search + Add */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <form onSubmit={handleSearch} className="flex flex-1 items-end gap-2">
              <div className="flex-1">
                <Label htmlFor="search" className="text-xs text-mute">Search masters</Label>
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-mute" />
                  <Input
                    id="search"
                    placeholder="MT-00001 or name"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>
              <Button type="submit" variant="outline">Search</Button>
              {search && <Button type="button" variant="ghost" onClick={() => { setSearch(""); load(); }}>Clear</Button>}
            </form>
            <Button onClick={() => setShowAdd(true)} className="shrink-0">
              <Plus className="mr-1.5 h-4 w-4" /> Add Program Record
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Masters table */}
      {loading ? (
        <LoadingState message="Loading trainees..." />
      ) : masters.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Users className="mx-auto h-10 w-10 text-mute/40" />
            <p className="mt-3 text-sm font-medium text-ink">No master trainees yet</p>
            <p className="mt-1 text-xs text-mute">Add your first program record to create a master (MT-xxxxx).</p>
            <Button className="mt-4" onClick={() => setShowAdd(true)}>Add Program Record</Button>
            <div className="mt-6 rounded-lg bg-canvas-soft2 p-4 text-left text-xs text-body">
              <p className="font-semibold text-ink">Demo scenario:</p>
              <p className="mt-1">1) Rahul Sharma — DOB 2003-05-12 — 9876543210 — PMKVY / PMK-10231 → creates MT-00001</p>
              <p>2) Rahul S Sharma — same DOB — 9123456780 — DDU-GKY / DDU-7841 → medium match (~70%) → review → Link</p>
              <p>3) Master MT-00001 then shows both programs.</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Master Trainees ({total})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-sm">
                <thead>
                  <tr className="border-b border-hairline text-left text-xs font-medium uppercase tracking-wide text-mute">
                    <th className="py-2 pr-4">Master ID</th>
                    <th className="py-2 pr-4">Name</th>
                    <th className="py-2 pr-4">DOB</th>
                    <th className="py-2 pr-4">Phones</th>
                    <th className="py-2 pr-4">Programs</th>
                    <th className="py-2 pr-4">Created</th>
                    <th className="py-2 pr-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {masters.map((m) => (
                    <tr key={m.id} className="border-b border-hairline last:border-0 hover:bg-canvas-soft/50">
                      <td className="py-3 pr-4 font-mono text-xs font-semibold text-ink">{m.master_code}</td>
                      <td className="py-3 pr-4 font-medium text-ink">{m.primary_name}</td>
                      <td className="py-3 pr-4 text-body">{m.dob ? new Date(m.dob).toLocaleDateString("en-GB") : "-"}</td>
                      <td className="py-3 pr-4 text-body">
                        <div className="flex flex-wrap gap-1">
                          {(m.masked_phones || []).map((p, i) => (
                            <Badge key={i} variant="secondary" className="text-[11px]">{p}</Badge>
                          ))}
                          {(!m.masked_phones || m.masked_phones.length === 0) && <span className="text-mute">—</span>}
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant="outline">{m.enrollment_count} program{m.enrollment_count !== 1 ? "s" : ""}</Badge>
                      </td>
                      <td className="py-3 pr-4 text-xs text-mute">{formatDate(m.created_at)}</td>
                      <td className="py-3 pr-4">
                        <Link href={`/admin/trainees/${m.id}`}>
                          <Button variant="ghost" size="sm" className="h-7 text-xs">
                            <Eye className="mr-1 h-3 w-3" /> View
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add dialog */}
      <Dialog open={showAdd} onOpenChange={(o) => !o && closeAdd()}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-[620px]">
          <DialogHeader>
            <DialogTitle>Add Trainee Program Record</DialogTitle>
            <DialogDescription>
              Create a program-specific record. System runs identity matching, then auto-links, flags for review, or creates a new master.
            </DialogDescription>
          </DialogHeader>

          {!result ? (
            <form onSubmit={handleAdd} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <Label htmlFor="name">Full Name *</Label>
                  <Input
                    id="name"
                    placeholder="Rahul Sharma"
                    value={form.trainee_name}
                    onChange={(e) => setForm({ ...form, trainee_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="dob">Date of Birth *</Label>
                  <Input
                    id="dob"
                    type="date"
                    value={form.dob}
                    onChange={(e) => setForm({ ...form, dob: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    placeholder="9876543210"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  />
                  <p className="mt-1 text-[11px] text-mute">Phone can change — mismatch does not auto-reject.</p>
                </div>
                <div>
                  <Label htmlFor="program">Program *</Label>
                  <select
                    id="program"
                    value={form.program_name}
                    onChange={(e) => setForm({ ...form, program_name: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="PMKVY">PMKVY</option>
                    <option value="DDU-GKY">DDU-GKY</option>
                    <option value="NAPS">NAPS</option>
                    <option value="PMKK">PMKK</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="pid">Program Trainee ID *</Label>
                  <Input
                    id="pid"
                    placeholder="PMK-10231"
                    value={form.program_trainee_id}
                    onChange={(e) => setForm({ ...form, program_trainee_id: e.target.value })}
                    required
                  />
                  <p className="mt-1 text-[11px] text-mute">Original program ID — never overwritten.</p>
                </div>
              </div>

              {error && (
                <div className="rounded-md bg-err-soft p-3 text-sm text-err-deep">{error}</div>
              )}

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={closeAdd}>Cancel</Button>
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Matching..." : "Run Identity Matching"}
                </Button>
              </div>
              <p className="text-center text-[11px] text-mute">
                Weights: Name 30% · DOB 30% · Phone 15% · Program 25% · thresholds 85%/60% (tunable)
              </p>
            </form>
          ) : (
            <div className="space-y-4">
              {/* Result */}
              <div
                className={`rounded-lg border p-4 ${
                  result.action === "auto_linked"
                    ? "border-link bg-link-soft/30"
                    : result.action === "review_required"
                    ? "border-warn bg-warn-soft/40"
                    : "border-hairline bg-canvas-soft"
                }`}
              >
                <div className="flex items-center gap-2">
                  {result.action === "auto_linked" && <CheckCircle className="h-5 w-5 text-link" />}
                  {result.action === "review_required" && <Clock className="h-5 w-5 text-warn-deep" />}
                  {result.action === "new_master" && <Users className="h-5 w-5 text-ink" />}
                  <p className="text-sm font-semibold text-ink">{result.message}</p>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-mute">Match Score: </span>
                    <span className={`font-mono font-semibold ${result.match_score >= 85 ? "text-link" : result.match_score >= 60 ? "text-warn-deep" : "text-mute"}`}>
                      {result.match_score}%
                    </span>
                    <Badge variant={result.confidence === "high" ? "success" : result.confidence === "medium" ? "warning" : "secondary"} className="ml-2 text-[10px]">
                      {result.confidence} confidence
                    </Badge>
                  </div>
                  <div className="text-right text-mute">Action: <span className="font-medium text-ink">{result.action}</span></div>
                </div>

                {/* Field scores */}
                <div className="mt-3 rounded-md bg-white/70 p-3">
                  <p className="text-xs font-medium text-ink">Field comparison (explainable):</p>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
                    <FieldScore label="Name" value={result.field_scores.name} />
                    <FieldScore label="DOB" value={result.field_scores.dob} />
                    <FieldScore label="Phone" value={result.field_scores.phone} />
                    <FieldScore label="Program" value={result.field_scores.program} />
                  </div>
                  <p className="mt-2 text-[11px] text-mute">
                    Program score neutral (0.5) for cross-program IDs — not globally comparable. Same program + same ID = 1.0, same program + different ID = 0.0.
                  </p>
                </div>

                {result.action === "review_required" && result.review && (
                  <div className="mt-3 rounded-md bg-white p-3 text-xs">
                    <p className="font-medium text-ink">Flagged for admin review</p>
                    <p className="mt-1 text-mute">Incoming: <span className="font-medium text-ink">{result.review.incoming_name}</span> · {result.review.incoming_program_name} / {result.review.incoming_program_trainee_id}</p>
                    {result.review.matched_master && (
                      <p className="mt-1 text-mute">
                        Possible match: <span className="font-medium text-ink">{result.review.matched_master.primary_name}</span> ({result.review.matched_master.master_code}) · {result.review.matched_master_enrollments.map((e: any) => `${e.program_name}/${e.program_trainee_id}`).join(", ")}
                      </p>
                    )}
                    <div className="mt-3 flex gap-2">
                      <Link href="/admin/identity-reviews">
                        <Button size="sm" variant="outline">Go to Reviews</Button>
                      </Link>
                      <Button size="sm" variant="ghost" onClick={closeAdd}>Close</Button>
                    </div>
                  </div>
                )}

                {(result.action === "new_master" || result.action === "auto_linked") && result.master && (
                  <div className="mt-3 flex items-center justify-between rounded-md bg-white p-3 text-xs">
                    <div>
                      <p className="font-semibold text-ink">{result.master.master_code} — {result.master.primary_name}</p>
                      <p className="text-mute">{result.record?.program_name} / {result.record?.program_trainee_id}</p>
                    </div>
                    <Link href={`/admin/trainees/${result.master.id}`}>
                      <Button size="sm">View Master</Button>
                    </Link>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={closeAdd}>Done</Button>
                <Button onClick={() => { setResult(null); setError(null); setForm({ trainee_name: "", dob: "", phone: "", program_name: "PMKVY", program_trainee_id: "" }); }}>
                  Add Another
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function FieldScore({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  let variant: "success" | "warning" | "secondary" | "destructive" = "secondary";
  if (value >= 0.9) variant = "success";
  else if (value >= 0.6) variant = "warning";
  else if (value === 0) variant = "secondary";
  else variant = "destructive";
  return (
    <div className="rounded border border-hairline bg-canvas-soft2 px-2 py-1.5 text-center">
      <p className="text-[11px] font-medium uppercase tracking-wide text-mute">{label}</p>
      <p className="font-mono text-sm font-semibold text-ink">{pct}%</p>
      <Badge variant={variant} className="mt-1 text-[10px] px-1.5 py-0">
        {value === 1 ? "exact" : value >= 0.9 ? "high" : value >= 0.5 ? "partial" : value === 0 ? "mismatch" : "low"}
      </Badge>
    </div>
  );
}
