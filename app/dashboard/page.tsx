"use client";

import { Check, CircleDashed, Inbox, List, Loader2, Plus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AssignmentCard } from "@/components/AssignmentCard";
import { CalendarWidget } from "@/components/CalendarWidget";
import { Navbar } from "@/components/Navbar";
import { StatCard } from "@/components/StatCard";
import { SyncStatus } from "@/components/SyncStatus";
import { createClient } from "@/lib/supabase/client";
import type {
  Assignment,
  AssignmentStatus,
  CalendarEvent,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const FILTERS: { label: string; value: AssignmentStatus | "all" }[] = [
  { label: "All", value: "all" },
  { label: "To do", value: "todo" },
  { label: "In progress", value: "in_progress" },
  { label: "Done", value: "done" },
];

export default function DashboardPage() {
  const supabase = useMemo(() => createClient(), []);
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string>("");
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [filter, setFilter] = useState<AssignmentStatus | "all">("all");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) {
      router.replace("/login");
      return;
    }
    setAccessToken(session.access_token);

    setLoading(true);
    const [a, e] = await Promise.all([
      supabase
        .from("assignments")
        .select("*, courses(name, course_code, color)")
        .order("due_at", { ascending: true, nullsFirst: false }),
      supabase
        .from("calendar_events")
        .select("*")
        .order("start_at", { ascending: true }),
    ]);
    if (a.data) setAssignments(a.data as Assignment[]);
    if (e.data) setEvents(e.data as CalendarEvent[]);
    setLoading(false);
  }, [supabase, router]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  async function setStatus(id: number, status: AssignmentStatus) {
    setAssignments((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status } : a)),
    );
    const { error } = await supabase
      .from("assignments")
      .update({ status })
      .eq("id", id);
    if (error) {
      // rollback by reloading
      loadAll();
    }
  }

  async function triggerSync() {
    if (!accessToken) return;
    setSyncing(true);
    setSyncMessage("Syncing Canvas…");
    try {
      const r = await fetch("/api/canvas/sync", {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const data = await r.json();
      if (r.ok) {
        setSyncMessage(
          `Synced ${data.courses ?? 0} courses, ${data.assignments ?? 0} assignments.`,
        );
        setLastSyncedAt(new Date().toISOString());
        loadAll();
      } else {
        setSyncMessage(data.detail ?? "Sync failed");
      }
    } catch (e: unknown) {
      setSyncMessage(e instanceof Error ? e.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  const filtered =
    filter === "all" ? assignments : assignments.filter((a) => a.status === filter);
  const todoCount = assignments.filter((a) => a.status === "todo").length;
  const doneCount = assignments.filter((a) => a.status === "done").length;

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-6xl px-5 py-8">
        <div className="space-y-6">
          {/* Hero */}
          <div className="mac-anim space-y-1">
            <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-blue-400">
              Today
            </div>
            <h1 className="text-5xl font-bold tracking-tightest">Your work</h1>
            <p className="text-zinc-400 tracking-tight">
              Everything due, in one place.
            </p>
          </div>

          {/* Stats */}
          <div className="flex gap-3">
            <StatCard
              label="To do"
              value={todoCount}
              accent="rgb(96,165,250)"
              icon={CircleDashed}
            />
            <StatCard
              label="Done"
              value={doneCount}
              accent="rgb(52,211,153)"
              icon={Check}
            />
            <StatCard
              label="Total"
              value={assignments.length}
              accent="rgb(245,245,247)"
              icon={List}
            />
          </div>

          {/* Sync */}
          <SyncStatus
            syncing={syncing}
            lastSyncedAt={lastSyncedAt}
            message={syncMessage}
            onSync={triggerSync}
          />

          {/* Two-column layout */}
          <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-5">
            <div className="space-y-3 min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold tracking-tighter">
                  Assignments
                </h2>
                <div className="flex-1" />
                <div className="mac-segmented">
                  {FILTERS.map((f) => (
                    <button
                      key={f.value}
                      onClick={() => setFilter(f.value)}
                      className={cn(
                        "mac-seg-btn",
                        filter === f.value && "mac-seg-btn-active",
                      )}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>

              {loading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
                </div>
              ) : filtered.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="space-y-2">
                  {filtered.map((a) => (
                    <AssignmentCard
                      key={a.id}
                      assignment={a}
                      onStatusChange={setStatus}
                    />
                  ))}
                </div>
              )}
            </div>

            <div>
              <CalendarWidget events={events} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div
        className="p-5 rounded-full mb-4"
        style={{ background: "rgba(127,127,127,0.08)" }}
      >
        <Inbox className="w-10 h-10 text-zinc-500" />
      </div>
      <h3 className="text-xl font-bold tracking-tighter">All clear</h3>
      <p className="text-zinc-400 text-sm max-w-xs mt-1 tracking-tight">
        Connect Canvas or upload a syllabus to start tracking work.
      </p>
      <Link href="/settings" className="mac-button mt-4">
        <Plus className="w-4 h-4" />
        Connect Canvas
      </Link>
    </div>
  );
}
