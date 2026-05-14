import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { accountService } from "@/services";
import { accountSchema } from "@/lib/validations";
import { Modal } from "@/components/Modal";
import { Pagination } from "@/components/Pagination";
import { SkeletonTable } from "@/components/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { fmtMoney, fmtDate } from "@/lib/utils";
import { Plus, Eye, Search, Lock, Unlock, X as XIcon } from "lucide-react";
import { useFilters } from "@/hooks/useFilters";
import { FilterBar, type FieldDef } from "@/components/FilterBar";

export function AccountsPage() {
  const { hasRole } = useAuth();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [openForm, setOpenForm] = useState(false);
  const [viewingId, setViewingId] = useState<number | null>(null);

  const { filters, setFilter, removeFilter, clear, sort, setSort, queryParams } = useFilters();

  const list = useQuery({
    queryKey: ["accounts", page, q, queryParams],
    queryFn: () => accountService.list({ page, size: 20, q, ...queryParams }),
  });

  const fields: FieldDef[] = [
    { field: "Balance", label: "Balance", type: "numeric" },
    {
      field: "AccountType",
      label: "Type",
      type: "enum",
      options: [
        { label: "savings", value: "savings" },
        { label: "checking", value: "checking" },
        { label: "fixed", value: "fixed" },
      ],
    },
  ];

  const sortOptions = [
    { label: "Balance ↑", value: "Balance_asc" },
    { label: "Balance ↓", value: "Balance_desc" },
    { label: "Created ↓", value: "CreatedAt_desc" },
  ];

  const create = useMutation({
    mutationFn: (d: any) => accountService.create(d),
    onSuccess: () => {
      toast.success("Account opened");
      setOpenForm(false);
      qc.invalidateQueries({ queryKey: ["accounts"] });
    },
  });

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: any }) =>
      accountService.setStatus(id, status),
    onSuccess: () => {
      toast.success("Status updated");
      qc.invalidateQueries({ queryKey: ["accounts"] });
    },
    onError: () => {
      qc.invalidateQueries({ queryKey: ["accounts"] });
    },
  });

  const f = useForm({ resolver: zodResolver(accountSchema) });

  const openCreate = () => {
    f.reset({
      CustomerID: undefined,
      BranchID: undefined,
      AccountType: "savings",
      Balance: 0,
      Currency: "USD",
    });
    setOpenForm(true);
  };

  const items: any[] = (list.data as any)?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="font-display text-3xl">Accounts</h1>
        {hasRole("manager", "teller") && (
          <button className="btn-primary" onClick={openCreate}>
            <Plus size={16} /> Open account
          </button>
        )}
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <Search size={16} className="text-ink/40" />
          <input
            className="input"
            placeholder="Search by account ID, number or customer name..."
            value={q}
            onChange={(e) => {
              setPage(1);
              setQ(e.target.value);
            }}
          />
        </div>
        <FilterBar
          fields={fields}
          filters={filters}
          setFilter={setFilter}
          removeFilter={removeFilter}
          sort={sort}
          setSort={setSort}
          sortOptions={sortOptions}
          onClear={clear}
        />
        {list.isLoading ? (
          <SkeletonTable />
        ) : (
          <table className="table-base">
            <thead>
              <tr>
                <th>ID</th><th>Number</th><th>Customer</th><th>Branch</th>
                <th>Type</th><th>Balance</th><th>Status</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.AccountID}>
                  <td>{a.AccountID}</td>
                  <td>{a.AccountNumber}</td>
                  <td>{a.CustomerName}</td>
                  <td>{a.BranchName}</td>
                  <td>{a.AccountType}</td>
                  <td>{fmtMoney(a.Balance ?? 0)}</td>
                  <td>
                    <span
                      className={`badge ${
                        a.Status === "active"
                          ? "bg-emerald-100 text-emerald-700"
                          : a.Status === "frozen"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {a.Status}
                    </span>
                  </td>
                  <td className="flex gap-2">
                    <button
                      className="text-blue-600 text-xs inline-flex items-center gap-1"
                      onClick={() => setViewingId(a.AccountID)}
                    >
                      <Eye size={14} /> Detail
                    </button>
                    {hasRole("manager") && a.Status === "active" && (
                      <button
                        className="text-amber-700 text-xs inline-flex items-center gap-1"
                        onClick={() =>
                          confirm("Freeze this account?") &&
                          setStatus.mutate({ id: a.AccountID, status: "frozen" })
                        }
                      >
                        <Lock size={14} /> Freeze
                      </button>
                    )}
                    {hasRole("manager") && a.Status === "frozen" && (
                      <button
                        className="text-emerald-700 text-xs inline-flex items-center gap-1"
                        onClick={() =>
                          setStatus.mutate({ id: a.AccountID, status: "active" })
                        }
                      >
                        <Unlock size={14} /> Unfreeze
                      </button>
                    )}
                    {hasRole("manager") && a.Status !== "closed" && (
                      <button
                        className="text-red-600 text-xs inline-flex items-center gap-1"
                        onClick={() => {
                          if (
                            confirm(
                              `Close account #${a.AccountID}? Balance must be $0.00 — current balance: ${fmtMoney(a.Balance ?? 0)}.`
                            )
                          ) {
                            setStatus.mutate({ id: a.AccountID, status: "closed" });
                          }
                        }}
                      >
                        <XIcon size={14} /> Close
                      </button>
                    )}
                  </td>
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

      <Modal open={openForm} onClose={() => setOpenForm(false)} title="Open new account">
        <form
          onSubmit={f.handleSubmit((d: any) => create.mutate(d))}
          className="space-y-3"
        >
          <div>
            <label className="label">CustomerID</label>
            <input className="input" type="number" {...f.register("CustomerID")} />
          </div>
          <div>
            <label className="label">BranchID</label>
            <input className="input" type="number" {...f.register("BranchID")} />
          </div>
          <div>
            <label className="label">Account type</label>
            <select className="input" {...f.register("AccountType")}>
              <option value="savings">savings</option>
              <option value="checking">checking</option>
              <option value="fixed">fixed</option>
            </select>
          </div>
          <div>
            <label className="label">Initial balance</label>
            <input className="input" type="number" step="0.01" {...f.register("Balance")} />
          </div>
          <div>
            <label className="label">Currency</label>
            <input className="input" {...f.register("Currency")} />
          </div>
          <button className="btn-primary w-full" disabled={create.isPending}>
            {create.isPending ? "Opening..." : "Open account"}
          </button>
        </form>
      </Modal>

      <AccountDetailModal id={viewingId} onClose={() => setViewingId(null)} />
    </div>
  );
}

function AccountDetailModal({
  id,
  onClose,
}: {
  id: number | null;
  onClose: () => void;
}) {
  const q = useQuery({
    queryKey: ["account", id],
    queryFn: () => accountService.get(id as number),
    enabled: !!id,
  });
  const a: any = q.data;
  return (
    <Modal open={!!id} onClose={onClose} title={a ? `Account #${a.AccountID}` : "Loading..."}>
      {q.isLoading || !a ? (
        <div className="text-sm text-ink/60">Loading...</div>
      ) : (
        <div className="space-y-3 text-sm">
          <div className="grid grid-cols-2 gap-2">
            <div><b>Number:</b> {a.AccountNumber}</div>
            <div><b>Customer:</b> {a.CustomerName}</div>
            <div><b>Branch:</b> {a.BranchName}</div>
            <div><b>Type:</b> {a.AccountType}</div>
            <div><b>Balance:</b> <span className="text-primary font-semibold">{fmtMoney(a.Balance ?? 0)}</span></div>
            <div><b>Currency:</b> {a.Currency}</div>
            <div><b>Status:</b> {a.Status}</div>
          </div>
          <div>
            <h4 className="font-semibold mt-3 mb-1">Recent transactions</h4>
            {(a.recent_transactions ?? []).length === 0 ? (
              <p className="text-ink/40 text-xs">No transactions found.</p>
            ) : (
              <table className="table-base text-xs">
                <thead>
                  <tr>
                    <th>ID</th><th>When</th><th>Type</th><th>Amount</th>
                    <th>Balance after</th><th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {(a.recent_transactions ?? []).map((t: any) => (
                    <tr key={t.TransactionID}>
                      <td>{t.TransactionID}</td>
                      <td>{fmtDate(t.CreatedAt)}</td>
                      <td>{t.TxType}</td>
                      <td>{fmtMoney(t.Amount)}</td>
                      <td>{fmtMoney(t.BalanceAfter ?? 0)}</td>
                      <td>{t.Description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </Modal>
  );
}
