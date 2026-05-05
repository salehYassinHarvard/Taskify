"use client";

import { Book, Calendar, Check, Star } from "lucide-react";
import { useState } from "react";

import { Assignment, AssignmentStatus } from "@/lib/types";
import { cn, formatDue, isOverdue } from "@/lib/utils";

const NEXT_STATUS: Record<AssignmentStatus, AssignmentStatus> = {
  todo: "in_progress",
  in_progress: "done",
  done: "todo",
};

interface Props {
  assignment: Assignment;
  onStatusChange: (id: number, status: AssignmentStatus) => Promise<void>;
}

export function AssignmentCard({ assignment, onStatusChange }: Props) {
  const [pending, setPending] = useState(false);

  const handleClick = async () => {
    setPending(true);
    try {
      await onStatusChange(
        assignment.id,
        NEXT_STATUS[assignment.status ?? "todo"],
      );
    } finally {
      setPending(false);
    }
  };

  const overdue =
    assignment.status !== "done" && isOverdue(assignment.due_at);

  const statusBadge = overdue
    ? {
        label: "Past due",
        classes: "bg-red-500/20 text-red-300 ring-red-400/30",
      }
    : {
        done: {
          label: "Done",
          classes: "bg-emerald-500/20 text-emerald-300 ring-emerald-400/30",
        },
        in_progress: {
          label: "In progress",
          classes: "bg-amber-500/20 text-amber-300 ring-amber-400/30",
        },
        todo: {
          label: "To do",
          classes: "bg-zinc-500/20 text-zinc-300 ring-zinc-400/20",
        },
      }[assignment.status ?? "todo"];

  const isPast = overdue || assignment.status === "done";

  return (
    <div
      className={cn(
        "mac-card mac-anim p-3 w-full",
        isPast && "opacity-70 hover:opacity-100 transition-opacity",
      )}
    >
      <div className="flex items-center gap-3">
        <button
          onClick={handleClick}
          disabled={pending}
          className="flex-shrink-0"
          aria-label={`Mark as ${NEXT_STATUS[assignment.status ?? "todo"]}`}
        >
          <StatusDisc status={assignment.status ?? "todo"} />
        </button>

        <div className="flex-1 min-w-0">
          <div
            className={cn(
              "font-medium text-[15px] tracking-tight truncate",
              assignment.status === "done" && "line-through text-zinc-500",
              overdue && "text-red-300/90",
            )}
          >
            {assignment.title}
          </div>
          <div className="flex items-center gap-3 mt-1 flex-wrap text-[12px] text-zinc-400">
            {assignment.courses?.name && (
              <Meta icon={<Book className="w-3 h-3" />}>
                {assignment.courses.name}
              </Meta>
            )}
            {assignment.due_at && (
              <Meta icon={<Calendar className="w-3 h-3" />}>
                {formatDue(assignment.due_at)}
              </Meta>
            )}
            {assignment.points_possible != null && (
              <Meta icon={<Star className="w-3 h-3" />}>
                {assignment.points_possible} pts
              </Meta>
            )}
          </div>
        </div>

        <span
          className={cn(
            "px-2.5 py-0.5 text-[11px] font-medium rounded-full ring-1 whitespace-nowrap",
            statusBadge.classes,
          )}
        >
          {statusBadge.label}
        </span>
      </div>
    </div>
  );
}

function Meta({
  icon,
  children,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <span className="inline-flex items-center gap-1">
      {icon}
      {children}
    </span>
  );
}

function StatusDisc({ status }: { status: AssignmentStatus }) {
  if (status === "done") {
    return (
      <div
        className="w-[22px] h-[22px] rounded-full flex items-center justify-center text-white"
        style={{
          background: "linear-gradient(180deg, #34d399, #10b981)",
          boxShadow: "0 1px 2px rgba(16,185,129,0.45)",
        }}
      >
        <Check className="w-3 h-3" strokeWidth={3} />
      </div>
    );
  }
  if (status === "in_progress") {
    return (
      <div
        className="w-[22px] h-[22px] rounded-full border-2 border-amber-500 box-border"
        style={{
          background: "conic-gradient(#f59e0b 0 65%, transparent 65%)",
        }}
      />
    );
  }
  return (
    <div className="w-[22px] h-[22px] rounded-full border-[1.5px] border-zinc-500 bg-transparent" />
  );
}
