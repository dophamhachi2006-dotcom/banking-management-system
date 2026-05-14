import { useQuery } from "@tanstack/react-query";
import { reportService } from "@/services";
import { Skeleton } from "@/components/Skeleton";
import { fmtMoney, fmtDate, fmtCompact } from "@/lib/utils";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from "recharts";

const PIE_COLORS = ["#0d7a5f", "#c9a84c", "#2563eb", "#dc2626", "#7c3aed", "#f97316"];

export function ReportsPage() {
  const top = useQuery({ queryKey: ["top"], queryFn: () => reportService.topCustomers(10) });
  const bp = useQuery({ queryKey: ["bp"], queryFn: () => reportService.branchPerf() });
  const breakdown = useQuery({ queryKey: ["breakdown"], queryFn: () => reportService.txBreakdown() });
  const fraud = useQuery({ queryKey: ["fraud-overview"], queryFn: () => reportService.fraud() });

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">Reports &amp; Analytics</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transaction type breakdown */}
        <div className="card">
          <h3 className="font-display text-xl mb-3">Transaction type breakdown</h3>
          {breakdown.isLoading ? (
            <Skeleton className="h-48" />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={(breakdown.data as any) ?? []}
                  dataKey="count"
                  nameKey="type"
                  outerRadius={100}
                  labelLine
                  label={({ type, percent }: any) => `${type} ${(Number(percent)*100).toFixed(0)}%`}
                >
                  {((breakdown.data as any) ?? []).map((_: any, i: number) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Branch performance — top 10 only */}
        <div className="card">
          <h3 className="font-display text-xl mb-3">Branch performance (top 10)</h3>
          {bp.isLoading ? (
            <Skeleton className="h-48" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={((bp.data as any) ?? []).slice(0, 10)}
                margin={{ left: 60, right: 20, top: 10, bottom: 70 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="BranchName"
                  angle={-35}
                  textAnchor="end"
                  interval={0}
                  height={90}
                  tick={{ fontSize: 11 }}
                />
                <YAxis width={70} tickFormatter={fmtCompact} />
                <Tooltip formatter={(v: any) => fmtMoney(Number(v))} />
                <Bar dataKey="TotalDeposits" name="Total Deposits" fill="#0d7a5f" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Top customers */}
      <div className="card">
        <h3 className="font-display text-xl mb-3">Top customers by balance</h3>
        {top.isLoading ? (
          <Skeleton className="h-24" />
        ) : (
          <table className="table-base">
            <thead>
              <tr>
                <th>#</th><th>Name</th><th>Total Balance</th><th>Accounts</th>
              </tr>
            </thead>
            <tbody>
              {((top.data as any[]) ?? []).map((r, i) => (
                <tr key={r.CustomerID}>
                  <td>{i + 1}</td>
                  <td>{r.FullName}</td>
                  <td>{fmtMoney(r.TotalBalance)}</td>
                  <td>{r.Accounts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Fraud overview */}
      <div className="card">
        <h3 className="font-display text-xl mb-3 text-red-700">
          Fraud detection overview
        </h3>
        {fraud.isLoading ? (
          <Skeleton className="h-24" />
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
              <div className="rounded-lg border p-3">
                <div className="text-xs text-ink/60">Large amount (30d)</div>
                <div className="text-2xl font-semibold text-red-700">
                  {(fraud.data as any)?.large_amount_count ?? 0}
                </div>
              </div>
              <div className="rounded-lg border p-3">
                <div className="text-xs text-ink/60">Late-night withdrawals</div>
                <div className="text-2xl font-semibold text-amber-700">
                  {(fraud.data as any)?.late_night_withdrawals ?? 0}
                </div>
              </div>
              <div className="rounded-lg border p-3">
                <div className="text-xs text-ink/60">Burst accounts (1h)</div>
                <div className="text-2xl font-semibold text-orange-700">
                  {(fraud.data as any)?.burst_accounts ?? 0}
                </div>
              </div>
            </div>
            <table className="table-base">
              <thead>
                <tr>
                  <th>TX</th><th>Account</th><th>Customer</th>
                  <th>Type</th><th>Amount</th><th>When</th>
                </tr>
              </thead>
              <tbody>
                {((fraud.data as any)?.recent ?? []).map((r: any) => (
                  <tr key={r.TransactionID}>
                    <td>{r.TransactionID}</td>
                    <td>{r.AccountNumber}</td>
                    <td>{r.CustomerName}</td>
                    <td>{r.TxType}</td>
                    <td>{fmtMoney(r.Amount)}</td>
                    <td>{fmtDate(r.CreatedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
}
