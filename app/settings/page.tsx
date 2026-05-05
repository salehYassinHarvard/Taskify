"use client";

import {
  CircleCheck,
  FileText,
  GraduationCap,
  Loader2,
  LogOut,
  TriangleAlert,
  User,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Navbar } from "@/components/Navbar";
import { SyllabusUpload } from "@/components/SyllabusUpload";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const supabase = useMemo(() => createClient(), []);
  const router = useRouter();
  const [accessToken, setAccessToken] = useState("");
  const [user, setUser] = useState<{
    email: string;
    name: string;
    avatar: string;
  } | null>(null);

  // Canvas state
  const [canvasUrl, setCanvasUrl] = useState("");
  const [canvasToken, setCanvasToken] = useState("");
  const [hasToken, setHasToken] = useState(false);
  const [coursesCount, setCoursesCount] = useState(0);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<{
    ok: boolean;
    message: string;
  } | null>(null);

  const loadStatus = useCallback(
    async (token: string) => {
      try {
        const r = await fetch("/api/canvas/status", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (r.ok) {
          const data = await r.json();
          setHasToken(!!data.has_token);
          setCoursesCount(data.courses_count ?? 0);
        }
      } catch {
        // ignore
      }
    },
    [],
  );

  useEffect(() => {
    (async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        router.replace("/login");
        return;
      }
      setAccessToken(session.access_token);
      setUser({
        email: session.user.email ?? "",
        name:
          (session.user.user_metadata?.full_name as string) ??
          (session.user.user_metadata?.name as string) ??
          "",
        avatar: (session.user.user_metadata?.avatar_url as string) ?? "",
      });
      loadStatus(session.access_token);
    })();
  }, [supabase, router, loadStatus]);

  async function saveCanvas() {
    if (!canvasUrl || !canvasToken) {
      setSaveResult({ ok: false, message: "Both URL and token are required." });
      return;
    }
    setSaving(true);
    setSaveResult(null);
    try {
      const r = await fetch("/api/canvas/token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ base_url: canvasUrl, token: canvasToken }),
      });
      const data = await r.json();
      if (r.ok && data.valid) {
        setSaveResult({
          ok: true,
          message: `Connected as ${data.user_name || "you"}. Click Sync on the dashboard to pull assignments.`,
        });
        setHasToken(true);
        setCanvasToken("");
      } else {
        setSaveResult({ ok: false, message: data.error ?? "Invalid token." });
      }
    } catch (e: unknown) {
      setSaveResult({
        ok: false,
        message: e instanceof Error ? e.message : "Error",
      });
    } finally {
      setSaving(false);
    }
  }

  async function disconnectCanvas() {
    try {
      await fetch("/api/canvas/token", {
        method: "DELETE",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setHasToken(false);
      setCoursesCount(0);
      setSaveResult({ ok: true, message: "Canvas disconnected." });
    } catch (e: unknown) {
      setSaveResult({
        ok: false,
        message: e instanceof Error ? e.message : "Error",
      });
    }
  }

  async function signOut() {
    await supabase.auth.signOut();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-3xl px-5 py-8">
        <div className="space-y-6">
          <div className="mac-anim space-y-1">
            <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-blue-400">
              Preferences
            </div>
            <h1 className="text-5xl font-bold tracking-tightest">Settings</h1>
            <p className="text-zinc-400 tracking-tight">
              Manage your integrations and account.
            </p>
          </div>

          {/* Canvas */}
          <Section
            icon={<GraduationCap className="w-[18px] h-[18px] text-blue-400" />}
            title="Canvas LMS"
            badge={
              <span
                className={cn(
                  "px-2.5 py-0.5 text-[11px] font-medium rounded-full ring-1",
                  hasToken
                    ? "bg-emerald-500/20 text-emerald-300 ring-emerald-400/30"
                    : "bg-zinc-500/20 text-zinc-400 ring-zinc-400/20",
                )}
              >
                {hasToken ? "Connected" : "Not connected"}
              </span>
            }
          >
            <p className="text-sm text-zinc-400">
              Paste a personal access token from Canvas → Account → Settings →
              New Access Token.
            </p>

            <div className="space-y-1">
              <label className="text-[12px] font-medium">Canvas URL</label>
              <input
                value={canvasUrl}
                onChange={(e) => setCanvasUrl(e.target.value)}
                placeholder="https://your-school.instructure.com"
                className="mac-input"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[12px] font-medium">Access Token</label>
              <input
                value={canvasToken}
                onChange={(e) => setCanvasToken(e.target.value)}
                type="password"
                placeholder="Canvas access token"
                className="mac-input"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={saveCanvas}
                disabled={saving}
                className="mac-button"
              >
                {saving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : null}
                Save & validate
              </button>
              {hasToken && (
                <button
                  onClick={disconnectCanvas}
                  className="mac-button-soft text-red-400"
                >
                  Disconnect
                </button>
              )}
            </div>

            {saveResult && (
              <div
                className={cn(
                  "flex items-start gap-2 text-sm rounded-lg p-3",
                  saveResult.ok
                    ? "bg-emerald-500/10 text-emerald-300 ring-1 ring-emerald-400/20"
                    : "bg-red-500/10 text-red-300 ring-1 ring-red-400/20",
                )}
              >
                {saveResult.ok ? (
                  <CircleCheck className="w-4 h-4 flex-shrink-0 mt-0.5" />
                ) : (
                  <TriangleAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
                )}
                <span>{saveResult.message}</span>
              </div>
            )}
            {coursesCount > 0 && (
              <div className="text-[11px] text-zinc-400">
                {coursesCount} courses synced.
              </div>
            )}
          </Section>

          {/* Syllabus */}
          <Section
            icon={<FileText className="w-[18px] h-[18px] text-blue-400" />}
            title="Syllabus parser"
          >
            <p className="text-sm text-zinc-400">
              Drop a syllabus PDF — Gemini extracts every assignment, due date,
              and point value automatically.
            </p>
            <SyllabusUpload accessToken={accessToken} />
          </Section>

          {/* Account */}
          <Section
            icon={<User className="w-[18px] h-[18px] text-blue-400" />}
            title="Account"
          >
            <div className="flex items-center gap-3">
              {user?.avatar ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={user.avatar}
                  alt={user.name || user.email}
                  className="w-12 h-12 rounded-full"
                />
              ) : (
                <div className="w-12 h-12 rounded-full bg-zinc-700 flex items-center justify-center text-white font-semibold">
                  {(user?.email?.[0] ?? "?").toUpperCase()}
                </div>
              )}
              <div className="flex-1">
                <div className="font-semibold tracking-tight">{user?.name}</div>
                <div className="text-sm text-zinc-400">{user?.email}</div>
              </div>
              <button
                onClick={signOut}
                className="mac-button-soft text-red-400"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign out
              </button>
            </div>
          </Section>
        </div>
      </main>
    </div>
  );
}

function Section({
  icon,
  title,
  badge,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  badge?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="mac-card mac-anim p-5 space-y-3">
      <div className="flex items-center gap-2">
        {icon}
        <h2 className="text-lg font-bold tracking-tighter">{title}</h2>
        {badge && <div className="ml-auto">{badge}</div>}
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  );
}
