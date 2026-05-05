import type { LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: number | string;
  accent: string; // CSS color for big number + icon
  icon: LucideIcon;
}

export function StatCard({ label, value, accent, icon: Icon }: Props) {
  return (
    <div className="mac-stat mac-anim p-4 flex-1 min-w-0">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-3.5 h-3.5" style={{ color: accent }} />
        <span className="text-[11px] uppercase tracking-[0.06em] text-zinc-400 font-medium">
          {label}
        </span>
      </div>
      <div
        className="text-[36px] font-bold leading-none tracking-tightest"
        style={{ color: accent }}
      >
        {value}
      </div>
    </div>
  );
}
