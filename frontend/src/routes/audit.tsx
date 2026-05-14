import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { auditService } from "@/services";
import { Pagination } from "@/components/Pagination";
import { SkeletonTable } from "@/components/Skeleton";
import { fmtDate } from "@/lib/utils";
import { Search } from "lucide-react";

const ACTIONS = ["", "INSERT", "UPDATE", "DELETE"];
const TABLES = [
  "", "Customers", "Accounts", "Transactions", "Loans",
  "CreditCards", "Employees", "Branches", "Users",
];

export function AuditPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<any>({});

  const list = useQuery({
    queryKey: ["audit", page, filters],
    queryFn: () => auditService.list({ page, size: 20, ...filters }),
  });
  const summary = useQuery({
    queryKey: ["audit-summary"],
    queryFn: () => auditService.summary(),
  });

  const items: any[] = (list.data as any)?.items ?? [];
  const s: any = summary.data ?? {};

  return (
    <div className="space-y-4">
      <h1 className="font-display text-3xl">Audit Log</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="font-display text-lg mb-2">By action</h3>
          <ul className="text-sm space-y-1">
            {(s.by_action ?? []).map((r: any) => (
              <li key={r.Action} className="flex justify-between">
                <span>{r.Action}</span>
                <span className="font-semibold">{r.c}</span>
              </li>
            ))}
            {(!s.by_action || s.by_action.length === 0) && (
              <li className="text-ink/50">No data</li>
            )}
          </ul>
        </div>
        <div className="card">
          <h3 className="font-display text-lg mb-2">By table</h3>
          <ul className="text-sm space-y-1">
            {(s.by_table ?? []).map((r: any) => (
              <li key={r.TableName} className="flex justify-between">
                <span>{r.TableName}</span>
                <span className="font-semibold">{r.c}</span>
              </li>
            ))}
            {(!s.by_table || s.by_table.length === 0) && (
              <li className="text-ink/50">No data</li>
            )}
          </ul>
        </div>
      </div>

      <div className="card">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-3">
          <div className="flex items-center gap-2 col-span-2">
            <Search size={16} className="text-ink/40" />
            <input
              className="input"
              placeholder="Search ID/table/action..."
              onChange={(e) => {
                setPage(1);
                setFilters({ ...filters, q: e.target.value || undefined });
              }}
            />
          </div>
          <select
            className="input"
            onChange={(e) => {
              setPage(1);
              setFilters({ ...filters, table: e.target.value || undefined });
            }}
          >
            {TABLES.map((t) => (
              <option key={t} value={t}>
                {t || "All tables"}
              </option>
            ))}
          </select>
          <select
            className="input"
            onChange={(e) => {
              setPage(1);
              setFilters({ ...filters, action: e.target.value || undefined });
            }}
          >
            {ACTIONS.map((a) => (
              <option key={a} value={a}>
                {a || "All actions"}
              </option>
            ))}
          </select>
          <input
            className="input"
            type="date"
            onChange={(e) =>
              setFilters({ ...filters, from: e.target.value || undefined })
            }
          />
        </div>

        {list.isLoading ? (
          <SkeletonTable />
        ) : (
          <table className="table-base">
            <thead>
              <tr>
                <th>ID</th><th>Table</th><th>Record</th><th>Action</th>
                <th>User</th><th>When</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r: any) => (
                <tr key={r.AuditID}>
                  <td>{r.AuditID}</td>
                  <td>{r.TableName}</td>
                  <td>{r.RecordID}</td>
                  <td>
                    <span
                      className={`badge ${
                        r.Action === "INSERT"
                          ? "bg-emerald-100 text-emerald-700"
                          : r.Action === "UPDATE"
                          ? "bg-amber-100 text-amber-700"
                          : r.Action === "DELETE"
                          ? "bg-red-100 text-red-700"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {r.Action}
                    </span>
                  </td>
                  <td>{r.PerformedByName ?? r.PerformedBy}</td>
                  <td>{fmtDate(r.CreatedAt)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <Pagination
          page={page}
          size={20}
          total={(list.data as any)?.total ?? 0}
          onPage={setPage}
        />
      </div>
    </div>
  );
}