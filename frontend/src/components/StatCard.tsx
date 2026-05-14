import { ReactNode } from "react";
import { fmtCompact } from "@/lib/utils";

const compact = (v: ReactNode): ReactNode => {
  if (typeof v === "number") return fmtCompact(v);
  return v;
};

export function StatCard({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  accent?: string;
}) {
  return (
    <div className="card flex items-center gap-4 min-w-0">
      {icon && (
        <div
          className="h-12 w-12 shrink-0 rounded-lg flex items-center justify-center"
          style={{ background: accent ?? "#0d7a5f15", color: "#0d7a5f" }}
        >
          {icon}
        </div>
      )}
      <div className="min-w-0 flex-1">
        <div className="text-xs uppercase text-ink/60 truncate">{label}</div>
        <div
          className="text-2xl font-display truncate"
          title={typeof value === "string" || typeof value === "number" ? String(value) : undefined}
        >
          {compact(value)}
        </div>
      </div>
    </div>
  );
}
