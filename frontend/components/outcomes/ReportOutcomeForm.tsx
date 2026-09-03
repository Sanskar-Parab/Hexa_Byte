"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, GraduationCap, Briefcase, CalendarClock, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type {
  OutcomeConsentState, TrainingProgram, TrainingEnrollment, EmploymentOutcome,
} from "@/types";

const selectClass =
  "w-full rounded-lg border border-hairline bg-canvas px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-ring";
const labelClass = "mb-1.5 block text-sm font-medium text-body";
const textareaClass =
  "w-full min-h-[70px] rounded-lg border border-hairline bg-canvas px-3 py-2 text-sm text-ink placeholder:text-mute focus:outline-none focus:ring-2 focus:ring-ring";

const EMPLOYMENT_STATUSES = [
  { value: "placed", label: "Placed" },
  { value: "employed", label: "Employed" },
  { value: "self_employed", label: "Self-employed" },
  { value: "looking_for_work", label: "Looking for work" },
  { value: "not_employed", label: "Not employed" },
];

interface ReportOutcomeFormProps {
  onUpdated: () => void;
}

export function ReportOutcomeForm({ onUpdated }: ReportOutcomeFormProps) {
  const [loading, setLoading] = useState(true);
  const [consent, setConsent] = useState<OutcomeConsentState | null>(null);
  const [programs, setPrograms] = useState<TrainingProgram[]>([]);
  const [enrollments, setEnrollments] = useState<TrainingEnrollment[]>([]);
  const [outcomes, setOutcomes] = useState<EmploymentOutcome[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [consentData, enrollmentData, outcomeData] = await Promise.all([
        api.getOutcomeConsent(),
        api.listEnrollments(),
        api.listEmploymentOutcomes(),
      ]);
      setConsent(consentData);
      setEnrollments(enrollmentData);
      setOutcomes(outcomeData);
    } catch {
      // Consent/timeline endpoints require auth already established by this point; a
      // failure here just means the form starts from an empty/unconsented state.
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleConsent = async (consented: boolean) => {
    setBusy(true);
    setError(null);
    try {
      const updated = await api.submitOutcomeConsent(consented);
      setConsent(updated);
    } catch (err: any) {
      setError(err.message || "Failed to update consent");
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center gap-2 p-6 text-sm text-body">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading...
        </CardContent>
      </Card>
    );
  }

  if (!consent?.consented) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
            <ShieldCheck className="h-4 w-4 text-mute" />
            Track Your Career Outcomes
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-body">
            Opt in to share your training completion, placement, and employment outcomes. This helps us give you
            better recommendations, and helps skilling programs and the government understand what&apos;s working.
            You can revoke this at any time — your existing records are never deleted.
          </p>
          {error && <p className="text-sm text-err-deep">{error}</p>}
          <Button onClick={() => handleConsent(true)} disabled={busy}>
            {busy ? "Saving..." : "I consent to outcome tracking"}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between rounded-lg border border-hairline bg-canvas-soft px-4 py-2.5 text-xs text-body">
        <span className="flex items-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-link" /> You&apos;ve consented to outcome tracking.
        </span>
        <button
          className="text-mute underline hover:text-ink"
          onClick={() => handleConsent(false)}
          disabled={busy}
        >
          Revoke consent
        </button>
      </div>

      <EnrollmentSection
        enrollments={enrollments}
        programs={programs}
        setPrograms={setPrograms}
        onEnrolled={async () => {
          await load();
          onUpdated();
        }}
      />

      <EmploymentSection
        enrollments={enrollments}
        outcomes={outcomes}
        onSubmitted={async () => {
          await load();
          onUpdated();
        }}
      />
    </div>
  );
}

function EnrollmentSection({
  enrollments,
  programs,
  setPrograms,
  onEnrolled,
}: {
  enrollments: TrainingEnrollment[];
  programs: TrainingProgram[];
  setPrograms: (p: TrainingProgram[]) => void;
  onEnrolled: () => void;
}) {
  const [showForm, setShowForm] = useState(enrollments.length === 0);
  const [selectedProgramId, setSelectedProgramId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (showForm && programs.length === 0) {
      api.listTrainingPrograms().then(setPrograms).catch(() => {});
    }
  }, [showForm, programs.length, setPrograms]);

  const handleSubmit = async () => {
    if (!selectedProgramId) return;
    setBusy(true);
    setError(null);
    try {
      await api.createEnrollment(selectedProgramId);
      setShowForm(false);
      setSelectedProgramId("");
      onEnrolled();
    } catch (err: any) {
      setError(err.message || "Failed to enroll");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base font-semibold text-ink">
          <span className="flex items-center gap-2">
            <GraduationCap className="h-4 w-4 text-mute" /> Training
          </span>
          {!showForm && (
            <Button variant="outline" size="sm" onClick={() => setShowForm(true)}>
              Enroll in a Program
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {enrollments.length > 0 && !showForm && (
          <div className="space-y-2">
            {enrollments.map((e) => {
              const program = programs.find((p) => p.id === e.training_program_id);
              return (
                <div key={e.id} className="rounded-lg border border-hairline p-3 text-sm">
                  <span className="font-medium text-ink">{program?.name || "Training program"}</span>
                  <span className="ml-2 capitalize text-mute">· {e.status.replace("_", " ")}</span>
                </div>
              );
            })}
          </div>
        )}

        {showForm && (
          <div className="space-y-3">
            {programs.length === 0 ? (
              <p className="text-sm text-mute">No training programs available yet.</p>
            ) : (
              <div>
                <label className={labelClass}>Training program</label>
                <select
                  className={selectClass}
                  value={selectedProgramId}
                  onChange={(e) => setSelectedProgramId(e.target.value)}
                >
                  <option value="">Select a program</option>
                  {programs.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} — {p.provider_name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {error && <p className="text-sm text-err-deep">{error}</p>}
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSubmit} disabled={busy || !selectedProgramId}>
                {busy ? "Enrolling..." : "Enroll"}
              </Button>
              {enrollments.length > 0 && (
                <Button size="sm" variant="ghost" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function EmploymentSection({
  enrollments,
  outcomes,
  onSubmitted,
}: {
  enrollments: TrainingEnrollment[];
  outcomes: EmploymentOutcome[];
  onSubmitted: () => void;
}) {
  const activeOutcome = outcomes.find((o) => !o.employment_end_date) || outcomes[0] || null;
  const [mode, setMode] = useState<"none" | "employment" | "checkin">("none");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base font-semibold text-ink">
          <span className="flex items-center gap-2">
            <Briefcase className="h-4 w-4 text-mute" /> Placement &amp; Employment
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setMode(mode === "employment" ? "none" : "employment")}>
              {activeOutcome ? "Update Employment" : "Report Placement"}
            </Button>
            {activeOutcome && (
              <Button variant="outline" size="sm" onClick={() => setMode(mode === "checkin" ? "none" : "checkin")}>
                <CalendarClock className="mr-1.5 h-3.5 w-3.5" /> Add Check-in
              </Button>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {activeOutcome && mode === "none" && (
          <div className="rounded-lg border border-hairline p-3 text-sm">
            <span className="font-medium capitalize text-ink">{activeOutcome.employment_status.replace("_", " ")}</span>
            {activeOutcome.job_title && <span className="ml-2 text-body">{activeOutcome.job_title}</span>}
            {activeOutcome.company_name && <span className="ml-1 text-mute">at {activeOutcome.company_name}</span>}
          </div>
        )}
        {!activeOutcome && mode === "none" && (
          <p className="text-sm text-mute">No employment outcome reported yet.</p>
        )}

        {mode === "employment" && (
          <EmploymentForm
            enrollments={enrollments}
            onDone={() => {
              setMode("none");
              onSubmitted();
            }}
            onCancel={() => setMode("none")}
          />
        )}

        {mode === "checkin" && activeOutcome && (
          <CheckInForm
            employmentOutcomeId={activeOutcome.id}
            onDone={() => {
              setMode("none");
              onSubmitted();
            }}
            onCancel={() => setMode("none")}
          />
        )}
      </CardContent>
    </Card>
  );
}

function EmploymentForm({
  enrollments,
  onDone,
  onCancel,
}: {
  enrollments: TrainingEnrollment[];
  onDone: () => void;
  onCancel: () => void;
}) {
  const [status, setStatus] = useState("placed");
  const [jobTitle, setJobTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [location, setLocation] = useState("");
  const [salary, setSalary] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.createEmploymentOutcome({
        training_enrollment_id: enrollments[0]?.id,
        employment_status: status,
        job_title: jobTitle || undefined,
        company_name: companyName || undefined,
        location: location || undefined,
        salary: salary ? Number(salary) : undefined,
        salary_currency: salary ? "INR" : undefined,
        salary_period: salary ? "annual" : undefined,
        employment_start_date: status === "employed" || status === "self_employed" || status === "placed"
          ? new Date().toISOString().slice(0, 10)
          : undefined,
      });
      onDone();
    } catch (err: any) {
      setError(err.message || "Failed to save");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className={labelClass}>Status</label>
          <select className={selectClass} value={status} onChange={(e) => setStatus(e.target.value)}>
            {EMPLOYMENT_STATUSES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass}>Job title (optional)</label>
          <Input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} placeholder="e.g. Frontend Developer" />
        </div>
        <div>
          <label className={labelClass}>Company (optional)</label>
          <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="e.g. Acme Corp" />
        </div>
        <div>
          <label className={labelClass}>Location (optional)</label>
          <Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Bengaluru" />
        </div>
        <div>
          <label className={labelClass}>Annual salary, ₹ (optional)</label>
          <Input type="number" min={0} value={salary} onChange={(e) => setSalary(e.target.value)} placeholder="e.g. 300000" />
        </div>
      </div>
      {error && <p className="text-sm text-err-deep">{error}</p>}
      <div className="flex gap-2">
        <Button size="sm" onClick={handleSubmit} disabled={busy}>
          {busy ? "Saving..." : "Save"}
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>Cancel</Button>
      </div>
    </div>
  );
}

function CheckInForm({
  employmentOutcomeId,
  onDone,
  onCancel,
}: {
  employmentOutcomeId: string;
  onDone: () => void;
  onCancel: () => void;
}) {
  const [status, setStatus] = useState("employed");
  const [stillEmployed, setStillEmployed] = useState(true);
  const [salary, setSalary] = useState("");
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.createCheckIn({
        employment_outcome_id: employmentOutcomeId,
        employment_status: status,
        still_employed: stillEmployed,
        salary: salary ? Number(salary) : undefined,
        salary_currency: salary ? "INR" : undefined,
        reason_for_leaving: !stillEmployed && reason ? reason : undefined,
        notes: notes || undefined,
      });
      onDone();
    } catch (err: any) {
      setError(err.message || "Failed to save check-in");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className={labelClass}>Current status</label>
          <select className={selectClass} value={status} onChange={(e) => setStatus(e.target.value)}>
            {EMPLOYMENT_STATUSES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass}>Still employed there?</label>
          <select
            className={selectClass}
            value={stillEmployed ? "yes" : "no"}
            onChange={(e) => setStillEmployed(e.target.value === "yes")}
          >
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </div>
        <div>
          <label className={labelClass}>Current annual salary, ₹ (optional)</label>
          <Input type="number" min={0} value={salary} onChange={(e) => setSalary(e.target.value)} />
        </div>
        {!stillEmployed && (
          <div>
            <label className={labelClass}>Reason for leaving (optional)</label>
            <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Never required — your call" />
          </div>
        )}
      </div>
      <div>
        <label className={labelClass}>Notes (optional)</label>
        <textarea className={textareaClass} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </div>
      {error && <p className="text-sm text-err-deep">{error}</p>}
      <div className="flex gap-2">
        <Button size="sm" onClick={handleSubmit} disabled={busy}>
          {busy ? "Saving..." : "Save Check-in"}
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>Cancel</Button>
      </div>
    </div>
  );
}
