"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Upload, FileText, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ResumeUploaderProps {
  onUploadComplete: (result: any) => void;
}

export function ResumeUploader({ onUploadComplete }: ResumeUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (f: File) => {
    setError(null);
    if (f.type !== "application/pdf") {
      setError("Only PDF files are supported.");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setError("File too large. Maximum size is 10MB.");
      return;
    }
    setFile(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const result = await (await import("@/lib/api")).api.uploadResume(file);
      onUploadComplete(result);
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div
          className={cn(
            "cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition-colors",
            dragOver ? "border-link bg-link-soft/40" : "border-hairline hover:border-hairline-strong",
            file && "border-link/40 bg-link-soft/20"
          )}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />

          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileText className="h-8 w-8 text-link" />
              <div className="text-left">
                <p className="font-medium text-ink">{file.name}</p>
                <p className="text-sm text-mute">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="mx-auto h-10 w-10 text-mute" />
              <p className="font-medium text-ink">Drop your resume here or click to browse</p>
              <p className="text-sm text-mute">PDF files up to 10MB</p>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-lg bg-err-soft px-4 py-2 text-sm text-err-deep">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        {file && (
          <Button onClick={handleUpload} disabled={uploading} className="mt-4 w-full">
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing Resume...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload &amp; Analyze
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
