import { useState, useMemo } from "react";

export type Operator = "gt" | "lt" | "eq" | "gte" | "lte" | "like" | "ne";
export type Filter = { op: Operator; value: string };
export type FilterState = Record<string, Filter>;

export function useFilters(initial: FilterState = {}) {
  const [filters, setFilters] = useState<FilterState>(initial);
  const [sort, setSort] = useState<string>(""); // e.g. "TotalBalance_desc"

  const setFilter = (field: string, patch: Partial<Filter>) => {
    setFilters((prev) => ({
      ...prev,
      [field]: { op: "eq", value: "", ...prev[field], ...patch },
    }));
  };

  const removeFilter = (field: string) => {
    setFilters((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  };

  const clear = () => {
    setFilters({});
    setSort("");
  };

  const queryParams = useMemo(() => {
    const p: Record<string, string> = {};
    Object.entries(filters).forEach(([field, f]) => {
      if (f.value === "" || f.value == null) return;
      p[`${field}_${f.op}`] = String(f.value);
    });
    if (sort) p.sort = sort;
    return p;
  }, [filters, sort]);

  return { filters, setFilter, removeFilter, clear, sort, setSort, queryParams };
}
