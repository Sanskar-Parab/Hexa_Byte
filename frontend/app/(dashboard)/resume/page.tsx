"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SectionHeader } from "@/components/ui/section-header";
import { LoadingState } from "@/components/ui/loading-state";
import { FileText, History, Trash2, Info } from "lucide-react";
import { api } from "@/lib/api";
import { ResumeUploader } from "@/components/resume/ResumeUploader";
import { ResumeResults } from "@/components/resume/ResumeResults";
import type { ResumeUploadResult, ResumeDetail } from "@/types";

export default function ResumePage() {
  const [uploadResult, setUploadResult] = useState<ResumeUploadResult | null>(null);
  const [resumes, setResumes] = useState<ResumeDetail[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadResumes();
  }, []);

  const loadResumes = async () => {
    try {
      const data = await api.getResumes();
      setResumes(data);
    } catch (err) {
      console.error("Failed to load resumes", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteResume(id);
      setResumes(resumes.filter((r) => r.id !== id));
    } catch (err) {
      console.error("Failed to delete resume", err);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <SectionHeader
        eyebrow="Resume"
        title="Resume Intelligence"
        description="Upload your resume to extract skills, projects, and experience — and turn them into evidence."
      />

      <div className="flex items-start gap-3 rounded-xl border border-warn/30 bg-warn-soft p-4">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-warn-deep" />
        <p className="text-sm text-warn-deep">
          Resume mentions are <strong>evidence</strong>, not proof of expert proficiency. Extracted
          skills are linked with MEDIUM confidence.
        </p>
      </div>

      {!uploadResult && <ResumeUploader onUploadComplete={setUploadResult} />}

      {uploadResult && (
        <div className="space-y-4">
          <ResumeResults result={uploadResult} />
          <Button
            variant="outline"
            onClick={() => {
              setUploadResult(null);
              loadResumes();
            }}
          >
            Upload Another Resume
          </Button>
        </div>
      )}

      {loading && <LoadingState message="Loading your resumes..." />}

      {!loading && resumes.length > 0 && !uploadResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-ink">
              <History className="h-4 w-4 text-mute" />
              Previous Uploads
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {resumes.map((resume) => (
                <div
                  key={resume.id}
                  className="flex items-center justify-between rounded-lg border border-hairline bg-canvas-soft p-3 transition-colors hover:bg-canvas-soft2"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-mute" />
                    <div>
                      <p className="text-sm font-medium text-ink">{resume.filename}</p>
                      <p className="text-xs text-mute">
                        {resume.matched_skills.length} skills detected
                        {" · "}
                        {new Date(resume.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(resume.id)}
                    className="text-mute hover:text-err"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
