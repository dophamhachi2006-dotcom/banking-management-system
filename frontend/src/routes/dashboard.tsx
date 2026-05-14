import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { reportService } from "@/services";
import { StatCard } from "@/components/StatCard";
import { Skeleton } from "@/components/Skeleton";
import {
  Users, CreditCard, ArrowLeftRight, Building2, Wallet, ShieldAlert,
} from "lucide-react";
import { fmtMoney, fmtMoneyCompact, fmtCompact, fmtMonth } from "@/lib/utils";
import {
  ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid,
  LineChart, Line, PieChart, Pie, Cell, Legend, BarChart, Bar,
} from "recharts";

const PIE_COLORS = ["#0d7a5f", "#c9a84c", "#2563eb", "#dc2626", "#7c3aed", "#f97316"];

const sortByMonth = (rows: any[]) =>
  [...rows].sort((a, b) => String(a.Month).localeCompare(String(b.Month)));

export function DashboardPage() {
  const stats = useQuery({ queryKey: ["dash"], queryFn: () => reportService.dashboard() });
  const monthly = useQuery({ queryKey: ["monthly"], queryFn: () => reportService.monthly() });
  const branches = useQuery({ queryKey: ["branchPerf"], queryFn: () => reportService.branchPerf() });
  const breakdown = useQuery({ queryKey: ["tx-breakdown"], queryFn: () => reportService.txBreakdown() });

  const monthlyData = useMemo(
    () => sortByMonth(((monthly.data as any) ?? []) as any[]),
    [monthly.data]
  );
  const branchData = useMemo(
    () => [...(((branches.data as any) ?? []) as any[])]
      .sort((a, b) => Number(b.TotalDeposits ?? 0) - Number(a.TotalDeposits ?? 0))
      .slice(0, 10),
    [branches.data]
  );

  if (stats.isLoading) return <Skeleton className="h-64" />;
  const s: any = stats.data || {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl">Dashboard Overview</h1>
        <p className="text-sm text-ink/60 mt-1">
          System-wide KPIs and activity trends across all branches.
        </p>
      </div>

      {/* KPI grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard label="Customers" value={s.customers} icon={<Users />} />
        <StatCard label="Accounts" value={s.accounts} icon={<CreditCard />} />
        <StatCard label="Active accounts" value={s.active_accounts} icon={<CreditCard />} />
        <StatCard label="Transactions" value={s.transactions} icon={<ArrowLeftRight />} />
        <StatCard label="Branches" value={s.branches} icon={<Building2 />} />
        <StatCard label="Total Assets" value={fmtMoneyCompact(s.total_assets ?? 0)} icon={<Wallet />} />
        <StatCard label="Today Tx" value={s.today_tx} icon={<ArrowLeftRight />} />
        <StatCard label="Today Volume" value={fmtMoneyCompact(s.today_volume ?? 0)} icon={<Wallet />} />
        <StatCard label="Active loans" value={s.active_loans ?? 0} icon={<ShieldAlert />} />
        <StatCard label="Loan outstanding" value={fmtMoneyCompact(s.loan_outstanding ?? 0)} icon={<Wallet />} />
      </div>

      {/* Monthly transaction volume chart */}
      <div className="card">
        <h3 className="font-display text-xl mb-3">Monthly transactions (volume)</h3>
        {monthlyData.length === 0 ? (
          <div className="text-sm text-ink/60 py-8 text-center">No transactions in the last 24 months.</div>
        ) : (
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={monthlyData} margin={{ left: 60, right: 20, top: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="Month" tickFormatter={fmtMonth} />
              <YAxis width={70} tickFormatter={fmtCompact} />
              <Tooltip
                labelFormatter={(l: any) => fmtMonth(String(l))}
                formatter={(v: any, name: any) =>
                  name === "Volume" ? fmtMoney(Number(v)) : Number(v).toLocaleString()
                }
              />
              <Legend />
              <Line type="monotone" dataKey="TotalAmount" name="Volume" stroke="#0d7a5f" strokeWidth={2.5} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="TxCount" name="Tx Count" stroke="#c9a84c" strokeWidth={2} dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Two-column charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-display text-xl mb-3">Branch deposits (top 10)</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={branchData} margin={{ left: 60, right: 20, top: 10, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="BranchName" angle={-30} textAnchor="end" height={80} interval={0} />
              <YAxis width={70} tickFormatter={fmtCompact} />
              <Tooltip formatter={(v: any) => fmtMoney(Number(v))} />
              <Legend />
              <Bar dataKey="TotalDeposits" name="Deposits" fill="#c9a84c" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="font-display text-xl mb-3">Transaction type mix</h3>
          <ResponsiveContainer width="100%" height={400}>
            <PieChart margin={{ top: 10, right: 60, bottom: 10, left: 60 }}>
              <Pie
                data={(breakdown.data as any) ?? []}
                dataKey="count"
                nameKey="type"
                outerRadius={110}
                labelLine
                label={({ type, percent }: any) =>
                  `${type} ${(Number(percent) * 100).toFixed(0)}%`
                }
              >
                {((breakdown.data as any) ?? []).map((_: any, i: number) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v: any) => Number(v).toLocaleString()} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
