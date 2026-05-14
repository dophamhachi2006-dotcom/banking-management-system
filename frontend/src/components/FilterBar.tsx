import { X } from "lucide-react";
import type { FilterState, Operator } from "@/hooks/useFilters";

export type FieldDef = {
  field: string;
  label: string;
  type: "numeric" | "string" | "enum" | "bool" | "date";
  operators?: Operator[];
  options?: { label: string; value: string }[];
};

const DEFAULT_OPS: Record<FieldDef["type"], Operator[]> = {
  numeric: ["gt", "lt", "eq", "gte", "lte"],
  string: ["like", "eq"],
  enum: ["eq"],
  bool: ["eq"],
  date: ["gte", "lte", "eq"],
};

const OP_LABEL: Record<Operator, string> = {
  gt: ">",
  lt: "<",
  eq: "=",
  gte: "≥",
  lte: "≤",
  like: "contains",
  ne: "≠",
};

export function FilterBar({
  fields,
  filters,
  setFilter,
  removeFilter,
  sort,
  setSort,
  sortOptions,
  onClear,
}: {
  fields: FieldDef[];
  filters: FilterState;
  setFilter: (field: string, patch: any) => void;
  removeFilter: (field: string) => void;
  sort: string;
  setSort: (s: string) => void;
  sortOptions: { label: string; value: string }[];
  onClear: () => void;
}) {
  return (
    <div className="card mb-3 space-y-3">
      <div className="flex flex-wrap gap-3">
        {fields.map((fd) => {
          const f = filters[fd.field];
          const ops = fd.operators ?? DEFAULT_OPS[fd.type];
          const inputType =
            fd.type === "numeric" ? "number" : fd.type === "date" ? "date" : "text";
          return (
            <div
              key={fd.field}
              className="flex items-center gap-1 border border-ink/10 rounded-md px-2 py-1 bg-white"
            >
              <span className="text-xs text-ink/60">{fd.label}</span>
              <select
                className="input !py-1 !px-1 text-xs !w-auto"
                value={f?.op ?? ops[0]}
                onChange={(e) => setFilter(fd.field, { op: e.target.value as Operator })}
              >
                {ops.map((o) => (
                  <option key={o} value={o}>
                    {OP_LABEL[o]}
                  </option>
                ))}
              </select>

              {fd.type === "enum" ? (
                <select
                  className="input !py-1 !px-1 text-xs !w-auto"
                  value={f?.value ?? ""}
                  onChange={(e) => setFilter(fd.field, { value: e.target.value })}
                >
                  <option value="">—</option>
                  {fd.options?.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              ) : fd.type === "bool" ? (
                <select
                  className="input !py-1 !px-1 text-xs !w-auto"
                  value={f?.value ?? ""}
                  onChange={(e) => setFilter(fd.field, { value: e.target.value })}
                >
                  <option value="">—</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              ) : (
                <input
                  className="input !py-1 !px-2 text-xs !w-32"
                  type={inputType}
                  value={f?.value ?? ""}
                  onChange={(e) => setFilter(fd.field, { value: e.target.value })}
                />
              )}

              {f?.value ? (
                <button
                  type="button"
                  onClick={() => removeFilter(fd.field)}
                  title="Clear"
                  className="text-ink/40 hover:text-red-600"
                >
                  <X size={14} />
                </button>
              ) : null}
            </div>
          );
        })}
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs text-ink/60">Sort by:</span>
        <select
          className="input !py-1 !px-2 text-xs !w-auto"
          value={sort}
          onChange={(e) => setSort(e.target.value)}
        >
          <option value="">— default —</option>
          {sortOptions.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <button type="button" className="btn-outline text-xs" onClick={onClear}>
          Clear all
        </button>
      </div>
    </div>
  );
}
