"use client";

import { Loader2, RefreshCw } from "lucide-react";

import { formatRelative } from "@/lib/utils";

interface Props {
  syncing: boolean;
  lastSyncedAt: string | null;
  message: string | null;
  onSync: () => void;
}

export function SyncStatus({ syncing, lastSyncedAt, message, onSync }: Props) {
  return (
    <div className="mac-card mac-anim p-3 w-full">
      <div className="flex items-center gap-3">
        {syncing ? (
          <div className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm font-medium">Syncing Canvas…</span>
          </div>
        ) : lastSyncedAt ? (
          <div className="flex items-center gap-2">
            <span
              className="w-2 h-2 rounded-full bg-emerald-400"
              style={{ boxShadow: "0 0 8px rgba(52,211,153,0.6)" }}
            />
            <span className="text-sm font-medium">Up to date</span>
            <span className="text-zinc-500">·</span>
            <span className="text-[11px] text-zinc-400">
              {formatRelative(lastSyncedAt)}
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-zinc-500" />
            <span className="text-sm text-zinc-400">Not yet synced</span>
          </div>
        )}

        <div className="flex-1" />

        {message && (
          <span className="text-[11px] text-zinc-500 italic mr-2">
            {message}
          </span>
        )}

        <button
          onClick={onSync}
          disabled={syncing}
          className="mac-button-soft text-[12px]"
        >
          <RefreshCw
            className={`w-[13px] h-[13px] ${syncing ? "animate-spin" : ""}`}
          />
          Sync
        </button>
      </div>
    </div>
  );
}
