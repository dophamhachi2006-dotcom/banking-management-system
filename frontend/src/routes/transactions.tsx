import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { transactionService } from "@/services";
import { txAmountSchema, transferSchema } from "@/lib/validations";
import { SkeletonTable } from "@/components/Skeleton";
import { Pagination } from "@/components/Pagination";
import { Modal } from "@/components/Modal";
import { useAuth } from "@/contexts/AuthContext";
import { fmtMoney, fmtDate } from "@/lib/utils";
import { useFilters } from "@/hooks/useFilters";
import { FilterBar, type FieldDef } from "@/components/FilterBar";

export function TransactionsPage() {
  const { hasRole } = useAuth();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<any>({});
  const [modal, setModal] = useState<null | "deposit" | "withdraw" | "transfer">(null);

  const dyn = useFilters();

  const list = useQuery({
    queryKey: ["tx", page, filters, dyn.queryParams],
    queryFn: () => transactionService.list({ page, size: 20, ...filters, ...dyn.queryParams }),
  });

  const dynFields: FieldDef[] = [
    { field: "Amount", label: "Amount", type: "numeric" },
    { field: "BalanceAfter", label: "Balance After", type: "numeric" },
    {
      field: "TxType",
      label: "Type",
      type: "enum",
      options: [
        { label: "deposit", value: "deposit" },
        { label: "withdrawal", value: "withdrawal" },
        { label: "transfer", value: "transfer" },
      ],
    },
  ];
  const dynSortOptions = [
    { label: "Amount ↑", value: "Amount_asc" },
    { label: "Amount ↓", value: "Amount_desc" },
    { label: "Balance After ↑", value: "BalanceAfter_asc" },
    { label: "Balance After ↓", value: "BalanceAfter_desc" },
    { label: "Created ↓", value: "CreatedAt_desc" },
  ];

  const action = useMutation({
    mutationFn: async (d: any) => {
      if (modal === "deposit")  return transactionService.deposit(d);
      if (modal === "withdraw") return transactionService.withdraw(d);
      return transactionService.transfer(d);
    },
    onSuccess: () => { toast.success("Done"); setModal(null); qc.invalidateQueries({ queryKey: ["tx"] }); },
  });

  const f = useForm({ resolver: zodResolver(modal === "transfer" ? transferSchema : txAmountSchema) });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="font-display text-3xl">Transactions</h1>
        {hasRole("manager","teller") && (
          <div className="flex gap-2">
            <button className="btn-primary" onClick={() => { f.reset(); setModal("deposit"); }}>+ Deposit</button>
            <button className="btn-outline" onClick={() => { f.reset(); setModal("withdraw"); }}>− Withdraw</button>
            <button className="btn-outline" onClick={() => { f.reset(); setModal("transfer"); }}>↔ Transfer</button>
          </div>
        )}
      </div>

      <div className="card grid grid-cols-2 md:grid-cols-5 gap-2">
        <input className="input" placeholder="Account ID"
               onChange={(e) => { setPage(1); setFilters({ ...filters, account_id: e.target.value || undefined }); }}/>
        <select className="input" onChange={(e) => { setPage(1); setFilters({ ...filters, type: e.target.value || undefined }); }}>
          <option value="">All types</option>
          {["deposit","withdrawal","transfer","fee","interest"].map(t=><option key={t}>{t}</option>)}
        </select>
        <input className="input" type="date" onChange={(e)=>setFilters({...filters, from: e.target.value || undefined})}/>
        <input className="input" type="date" onChange={(e)=>setFilters({...filters, to: e.target.value || undefined})}/>
        <input className="input" placeholder="Min amount" onChange={(e)=>setFilters({...filters, min_amount: e.target.value || undefined})}/>
        <input className="input md:col-span-5" placeholder="Search by tx ID, account number, customer name or description..." onChange={(e)=>{ setPage(1); setFilters({...filters, q: e.target.value || undefined}); }}/>
      </div>

      <FilterBar
        fields={dynFields}
        filters={dyn.filters}
        setFilter={dyn.setFilter}
        removeFilter={dyn.removeFilter}
        sort={dyn.sort}
        setSort={dyn.setSort}
        sortOptions={dynSortOptions}
        onClear={dyn.clear}
      />

      <div className="card">
        {list.isLoading ? <SkeletonTable/> : (
          <table className="table-base">
            <thead><tr>
              <th>ID</th><th>Account</th><th>Customer</th><th>Type</th>
              <th>Amount</th><th>Balance After</th><th>When</th>
            </tr></thead>
            <tbody>{(list.data as any)?.items?.map((t: any) => (
              <tr key={t.TransactionID}>
                <td>{t.TransactionID}</td><td>{t.AccountNumber}</td><td>{t.CustomerName}</td>
                <td><span className="badge bg-primary/10 text-primary">{t.TxType}</span></td>
                <td>{fmtMoney(t.Amount)}</td><td>{fmtMoney(t.BalanceAfter ?? 0)}</td>
                <td>{fmtDate(t.CreatedAt)}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
        <Pagination page={page} size={20} total={(list.data as any)?.total ?? 0} onPage={setPage}/>
      </div>

      <Modal open={!!modal} onClose={() => setModal(null)} title={modal ?? ""}>
        <form onSubmit={f.handleSubmit((d:any) => action.mutate(d))} className="space-y-3">
          {modal === "transfer" ? (
            <>
              <div><label className="label">From AccountID</label><input className="input" {...f.register("FromAccountID")}/></div>
              <div><label className="label">To AccountID</label><input className="input" {...f.register("ToAccountID")}/></div>
            </>
          ) : (
            <div><label className="label">AccountID</label><input className="input" {...f.register("AccountID")}/></div>
          )}
          <div><label className="label">Amount</label><input className="input" {...f.register("Amount")}/></div>
          <div><label className="label">Description</label><input className="input" {...f.register("Description")}/></div>
          <button className="btn-primary w-full" disabled={action.isPending}>
            {action.isPending ? "Processing..." : "Submit"}
          </button>
        </form>
      </Modal>
    </div>
  );
}
