import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDue(iso: string | null | undefined): string {
  if (!iso) return "No due date";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;

  const now = new Date();
  const sameYear = d.getFullYear() === now.getFullYear();

  const date = d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: sameYear ? undefined : "numeric",
  });
  const time = d.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${date} · ${time}`;
}

export function isOverdue(iso: string | null | undefined): boolean {
  if (!iso) return false;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return false;
  return d.getTime() < Date.now();
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;

  const diffMs = d.getTime() - Date.now();
  const diffMin = Math.round(diffMs / 60_000);
  const absMin = Math.abs(diffMin);

  if (absMin < 1) return "just now";
  if (absMin < 60) return diffMin > 0 ? `in ${absMin}m` : `${absMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (Math.abs(diffHr) < 24)
    return diffHr > 0 ? `in ${diffHr}h` : `${Math.abs(diffHr)}h ago`;
  const diffDay = Math.round(diffHr / 24);
  if (Math.abs(diffDay) < 7)
    return diffDay > 0 ? `in ${diffDay}d` : `${Math.abs(diffDay)}d ago`;
  return formatDue(iso);
}
