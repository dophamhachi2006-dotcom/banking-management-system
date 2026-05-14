import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { cardService, customerService } from "@/services";
import { cardSchema } from "@/lib/validations";
import { Modal } from "@/components/Modal";
import { Pagination } from "@/components/Pagination";
import { SkeletonTable } from "@/components/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { fmtMoney, fmtDate } from "@/lib/utils";
import { Plus, Lock, Unlock, History, Search } from "lucide-react";
import { useFilters } from "@/hooks/useFilters";
import { FilterBar, type FieldDef } from "@/components/FilterBar";

export function CardsPage() {
  const { hasRole } = useAuth();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [openForm, setOpenForm] = useState(false);
  const [historyCardId, setHistoryCardId] = useState<number | null>(null);

  const { filters, setFilter, removeFilter, clear, sort, setSort, queryParams } = useFilters();

  const list = useQuery({
    queryKey: ["cards", page, q, queryParams],
    queryFn: () => cardService.list({ page, size: 20, q, ...queryParams }),
  });

  // Load customers for the "Issue card" dropdown — prevents the user from
  // typing a non-existent CustomerID (which causes MySQL FK 1452).
  const customers = useQuery({
    queryKey: ["customers-for-cards"],
    queryFn: () => customerService.list({ page: 1, size: 500 }),
    enabled: openForm,
  });
  const customerOptions: any[] = (customers.data as any)?.items ?? [];

  const fields: FieldDef[] = [
    { field: "CreditLimit", label: "Limit", type: "numeric" },
    { field: "OutstandingBalance", label: "Outstanding", type: "numeric" },
    {
      field: "Status", label: "Status", type: "enum",
      options: [
        { label: "active", value: "active" },
        { label: "blocked", value: "blocked" },
      ],
    },
    { field: "HasTransactions", label: "Has tx", type: "bool" },
  ];
  const sortOptions = [
    { label: "Limit ↑", value: "CreditLimit_asc" },
    { label: "Limit ↓", value: "CreditLimit_desc" },
    { label: "Outstanding ↑", value: "OutstandingBalance_asc" },
    { label: "Outstanding ↓", value: "OutstandingBalance_desc" },
  ];

  const create = useMutation({
    mutationFn: (d: any) => cardService.create(d),
    onSuccess: () => {
      toast.success("Card issued");
      setOpenForm(false);
      qc.invalidateQueries({ queryKey: ["cards"] });
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.message ||
        err?.response?.data?.error ||
        err?.message ||
        "Failed to issue card";
      toast.error(msg);
    },
  });

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: any }) =>
      cardService.setStatus(id, status),
    onSuccess: () => {
      toast.success("Card status updated");
      qc.invalidateQueries({ queryKey: ["cards"] });
    },
  });

  const f = useForm({ resolver: zodResolver(cardSchema) });
  const items: any[] = (list.data as any)?.items ?? [];

  const onSubmit = (d: any) => {
    const payload: any = {
      ...d,
      CustomerID: Number(d.CustomerID),
      CreditLimit: Number(d.CreditLimit),
    };
    if (!payload.CustomerID) {
      toast.error("Please select a customer");
      return;
    }
    if (!payload.CreditLimit || payload.CreditLimit <= 0) {
      toast.error("Credit limit must be a positive number");
      return;
    }
    create.mutate(payload);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="font-display text-3xl">Credit Cards</h1>
        {hasRole("manager") && (
          <button
            className="btn-primary"
            onClick={() => {
              f.reset();
              setOpenForm(true);
            }}
          >
            <Plus size={16} /> Issue card
          </button>
        )}
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <Search size={16} className="text-ink/40" />
          <input
            className="input"
            placeholder="Search by card ID, number or customer name..."
            value={q}
            onChange={(e) => {
              setPage(1);
              setQ(e.target.value);
            }}
          />
        </div>
        <FilterBar fields={fields} filters={filters} setFilter={setFilter} removeFilter={removeFilter} sort={sort} setSort={setSort} sortOptions={sortOptions} onClear={clear} />
        {list.isLoading ? (
          <SkeletonTable />
        ) : (
          <table className="table-base">
            <thead>
              <tr>
                <th>ID</th><th>Number</th><th>Customer</th>
                <th>Limit</th><th>Outstanding</th><th>Expiry</th>
                <th>Status</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((c) => (
                <tr key={c.CardID}>
                  <td>{c.CardID}</td>
                  <td>{c.CardNumber}</td>
                  <td title={c.CustomerName || ""}>{c.CustomerName && String(c.CustomerName).trim() ? c.CustomerName : `Customer #${c.CustomerID}`}</td>
                  <td>{fmtMoney(c.CreditLimit)}</td>
                  <td>{fmtMoney(c.OutstandingBal ?? 0)}</td>
                  <td>{c.ExpiryDate ? fmtDate(c.ExpiryDate) : "—"}</td>
                  <td>
                    <span
                      className={`badge ${
                        c.Status === "active"
                          ? "bg-emerald-100 text-emerald-700"
                          : c.Status === "blocked"
                          ? "bg-red-100 text-red-700"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {c.Status}
                    </span>
                  </td>
                  <td className="flex gap-2">
                    <button
                      className="text-blue-600 text-xs inline-flex items-center gap-1"
                      onClick={() => setHistoryCardId(c.CardID)}
                    >
                      <History size={14} /> History
                    </button>
                    {hasRole("manager") && c.Status === "active" && (
                      <button
                        className="text-red-600 text-xs inline-flex items-center gap-1"
                        onClick={() =>
                          setStatus.mutate({ id: c.CardID, status: "blocked" })
                        }
                      >
                        <Lock size={14} /> Block
                      </button>
                    )}
                    {hasRole("manager") && c.Status === "blocked" && (
                      <button
                        className="text-emerald-700 text-xs inline-flex items-center gap-1"
                        onClick={() =>
                          setStatus.mutate({ id: c.CardID, status: "active" })
                        }
                      >
                        <Unlock size={14} /> Unblock
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

      <Modal open={openForm} onClose={() => setOpenForm(false)} title="Issue new credit card">
        <form onSubmit={f.handleSubmit(onSubmit)} className="space-y-3">
          <div>
            <label className="label">Customer</label>
            <select className="input" {...f.register("CustomerID")}>
              <option value="">
                {customers.isLoading ? "Loading customers…" : "Select customer…"}
              </option>
              {customerOptions.map((c) => (
                <option key={c.CustomerID} value={c.CustomerID}>
                  #{c.CustomerID} · {c.FullName ?? c.Name ?? ""}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Credit limit</label>
            <input className="input" type="number" step="0.01" min="0.01" {...f.register("CreditLimit")} />
          </div>
          <div>
            <label className="label">Expiry date</label>
            <input className="input" type="date" {...f.register("ExpiryDate")} />
          </div>
          <div>
            <label className="label">Card number (optional, auto if empty)</label>
            <input className="input" {...f.register("CardNumber")} />
          </div>
          <button className="btn-primary w-full" disabled={create.isPending}>
            {create.isPending ? "Issuing..." : "Issue card"}
          </button>
        </form>
      </Modal>

      <CardHistoryModal id={historyCardId} onClose={() => setHistoryCardId(null)} />
    </div>
  );
}

function CardHistoryModal({
  id,
  onClose,
}: {
  id: number | null;
  onClose: () => void;
}) {
  const q = useQuery({
    queryKey: ["card-tx", id],
    queryFn: () => cardService.transactions(id as number),
    enabled: !!id,
  });
  const rows: any[] = (q.data as any) ?? [];
  return (
    <Modal open={!!id} onClose={onClose} title={`Card #${id} transactions`}>
      {rows.length === 0 ? (
        <div className="text-sm text-ink/60">No transactions recorded.</div>
      ) : (
        <table className="table-base text-xs">
          <thead>
            <tr>
              <th>ID</th><th>When</th><th>Merchant</th><th>Amount</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t: any) => (
              <tr key={t.TransactionID ?? t.ID}>
                <td>{t.TransactionID ?? t.ID}</td>
                <td>{fmtDate(t.CreatedAt)}</td>
                <td>{t.Merchant ?? t.Description ?? "—"}</td>
                <td>{fmtMoney(t.Amount)}</td>
                <td>{t.Status ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Modal>
  );
}
