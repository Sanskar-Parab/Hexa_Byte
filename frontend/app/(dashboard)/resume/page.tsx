"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, History, Trash2 } from "lucide-react";
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
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <FileText className="h-6 w-6 text-blue-600" />
          Resume Intelligence
        </h1>
        <p className="text-slate-600 mt-1">
          Upload your resume to extract skills and create evidence records.
        </p>
      </div>

      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="p-4">
          <p className="text-sm text-amber-800">
            <strong>Important:</strong> Resume mentions are <strong>evidence</strong>, not proof
            of expert proficiency. Extracted skills are linked with MEDIUM confidence.
          </p>
        </CardContent>
      </Card>

      {!uploadResult && (
        <ResumeUploader onUploadComplete={setUploadResult} />
      )}

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

      {resumes.length > 0 && !uploadResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <History className="h-5 w-5 text-slate-500" />
              Previous Uploads
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {resumes.map((resume) => (
                <div
                  key={resume.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-slate-400" />
                    <div>
                      <p className="font-medium text-sm text-slate-800">{resume.filename}</p>
                      <p className="text-xs text-slate-500">
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
                    className="text-slate-400 hover:text-rose-600"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {loading && (
        <div className="text-center text-slate-500 py-8">Loading...</div>
      )}
    </div>
  );
}
