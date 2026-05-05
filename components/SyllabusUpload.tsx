"use client";

import { CloudUpload, Loader2, CircleCheck, TriangleAlert } from "lucide-react";
import { useRef, useState } from "react";

interface Props {
  accessToken: string;
  onParsed?: () => void;
}

interface ParseResult {
  ok: boolean;
  message: string;
}

export function SyllabusUpload({ accessToken, onParsed }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ParseResult | null>(null);

  async function handleFile(file: File) {
    if (file.type !== "application/pdf") {
      setResult({ ok: false, message: "Only PDF files are accepted." });
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setResult({ ok: false, message: "PDF must be 10 MB or smaller." });
      return;
    }

    setUploading(true);
    setResult(null);

    const fd = new FormData();
    fd.append("file", file);

    try {
      const r = await fetch("/api/syllabus/parse", {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
        body: fd,
      });
      if (!r.ok) {
        const detail = await r.json().catch(() => ({}));
        throw new Error(detail.detail ?? `HTTP ${r.status}`);
      }
      const data = await r.json();
      setResult({
        ok: true,
        message: `Parsed ${data?.course?.name ?? "syllabus"} — added ${
          data?.assignments_count ?? 0
        } assignments.`,
      });
      onParsed?.();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Upload failed";
      setResult({ ok: false, message: msg });
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const f = e.dataTransfer.files?.[0];
          if (f) handleFile(f);
        }}
        className={`border-[1.5px] border-dashed rounded-mac p-6 cursor-pointer transition text-center ${
          dragOver
            ? "border-blue-400 bg-blue-500/10"
            : "border-zinc-600 hover:bg-white/[0.03]"
        }`}
      >
        <CloudUpload className="w-7 h-7 text-blue-400 mx-auto mb-2" />
        <div className="text-sm font-medium">
          Drop a PDF here, or click to choose
        </div>
        <div className="text-[11px] text-zinc-400 mt-1">
          Up to 10 MB · PDF only
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
            e.target.value = "";
          }}
        />
      </div>

      {uploading && (
        <div className="mt-3 flex items-center gap-2 text-sm text-zinc-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          Parsing with Gemini…
        </div>
      )}

      {result && (
        <div
          className={`mt-3 flex items-start gap-2 text-sm rounded-lg p-3 ${
            result.ok
              ? "bg-emerald-500/10 text-emerald-300 ring-1 ring-emerald-400/20"
              : "bg-red-500/10 text-red-300 ring-1 ring-red-400/20"
          }`}
        >
          {result.ok ? (
            <CircleCheck className="w-4 h-4 flex-shrink-0 mt-0.5" />
          ) : (
            <TriangleAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
          )}
          <span>{result.message}</span>
        </div>
      )}
    </div>
  );
}
