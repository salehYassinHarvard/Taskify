"use client";

import { CalendarDays, CalendarX } from "lucide-react";

import { CalendarEvent } from "@/lib/types";
import { formatDue } from "@/lib/utils";

export function CalendarWidget({ events }: { events: CalendarEvent[] }) {
  return (
    <div className="mac-card mac-anim p-4 w-full">
      <div className="flex items-center gap-2 mb-3">
        <CalendarDays className="w-[15px] h-[15px] text-blue-400" />
        <span className="font-bold text-[15px] tracking-tight">Upcoming</span>
        <div className="flex-1" />
        <span className="text-[11px] text-zinc-500">{events.length}</span>
      </div>

      <div className="border-t border-white/5 dark:border-white/5 [html:not(.dark)_&]:border-black/5 mb-2" />

      {events.length > 0 ? (
        <div className="space-y-0">
          {events.slice(0, 8).map((e) => (
            <div
              key={e.gcal_event_id}
              className="flex items-center gap-3 py-2 px-2 rounded-lg transition hover:bg-white/[0.04]"
            >
              <div
                className="w-[3px] h-[42px] rounded-full"
                style={{
                  background:
                    "linear-gradient(180deg, rgb(91,139,248), rgb(124,109,223))",
                }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium tracking-tight truncate">
                  {e.summary}
                </div>
                <div className="text-[11px] text-zinc-400">
                  {formatDue(e.start_at)}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <CalendarX className="w-7 h-7 text-zinc-500 mb-2" />
          <div className="text-sm text-zinc-400 font-medium">
            No upcoming events
          </div>
          <div className="text-[11px] text-zinc-500 mt-0.5">
            Events from your Google Calendar will appear here.
          </div>
        </div>
      )}
    </div>
  );
}
