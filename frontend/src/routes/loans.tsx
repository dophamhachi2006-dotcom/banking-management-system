import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { loanService } from "@/services";
import { loanSchema, loanPaymentSchema } from "@/lib/validations";
import { Modal } from "@/components/Modal";
import { Pagination } from "@/components/Pagination";
import { SkeletonTable } from "@/components/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { fmtMoney } from "@/lib/utils";
import { Plus, Calculator, CreditCard, Search } from "lucide-react";
import { useFilters } from "@/hooks/useFilters";
import { FilterBar, type FieldDef } from "@/components/FilterBar";

export function LoansPage() {
  const { hasRole } = useAuth();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [openForm, setOpenForm] = useState(false);
  const [payingLoan, setPayingLoan] = useState<any>(null);
  const [interestLoanId, setInterestLoanId] = useState<number | null>(null);

  const { filters, setFilter, removeFilter, clear, sort, setSort, queryParams } = useFilters();

  const list = useQuery({
    queryKey: ["loans", page, q, queryParams],
    queryFn: () => loanService.list({ page, size: 20, q, ...queryParams }),
  });

  const fields: FieldDef[] = [
    { field: "Principal", label: "Principal", type: "numeric" },
    { field: "InterestRate", label: "Rate %", type: "numeric" },
    { field: "TermMonths", label: "Term", type: "numeric" },
    { field: "OutstandingBalance", label: "Outstanding", type: "numeric" },
    {
      field: "Status",
      label: "Status",
      type: "enum",
      options: [
        { label: "active", value: "active" },
        { label: "closed", value: "closed" },
        { label: "pending", value: "pending" },
      ],
    },
  ];
  const sortOptions = [
    { label: "Principal ↑", value: "Principal_asc" },
    { label: "Principal ↓", value: "Principal_desc" },
    { label: "Rate ↑", value: "InterestRate_asc" },
    { label: "Rate ↓", value: "InterestRate_desc" },
    { label: "Term ↑", value: "TermMonths_asc" },
    { label: "Term ↓", value: "TermMonths_desc" },
    { label: "Outstanding ↑", value: "OutstandingBalance_asc" },
    { label: "Outstanding ↓", value: "OutstandingBalance_desc" },
  ];

  const create = useMutation({
    mutationFn: (d: any) => loanService.create(d),
    onSuccess: () => {
      toast.success("Loan created");
      setOpenForm(false);
      qc.invalidateQueries({ queryKey: ["loans"] });
    },
  });

  const pay = useMutation({
    mutationFn: ({ id, amount }: { id: number; amount: number }) =>
      loanService.pay(id, amount),
    onSuccess: () => {
      toast.success("Payment recorded");
      setPayingLoan(null);
      qc.invalidateQueries({ queryKey: ["loans"] });
    },
  });

  const fNew = useForm({ resolver: zodResolver(loanSchema) });
  const fPay = useForm({ resolver: zodResolver(loanPaymentSchema) });

  const items: any[] = (list.data as any)?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="font-display text-3xl">Loans</h1>
        {hasRole("manager") && (
          <button
            className="btn-primary"
            onClick={() => {
              fNew.reset();
              setOpenForm(true);
            }}
          >
            <Plus size={16} /> New loan
          </button>
        )}
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <Search size={16} className="text-ink/40" />
          <input
            className="input"
            placeholder="Search by loan ID, customer ID or name..."
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
                <th>ID</th><th>Customer</th><th>Principal</th><th>Rate %</th>
                <th>Term</th><th>Outstanding</th><th>Status</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((l) => (
                <tr key={l.LoanID}>
                  <td>{l.LoanID}</td>
                  <td>{l.CustomerName}</td>
                  <td>{fmtMoney(l.Principal)}</td>
                  <td>{l.InterestRate}</td>
                  <td>{l.TermMonths}m</td>
                  <td>{fmtMoney(l.Outstanding ?? l.Principal)}</td>
                  <td>
                    <span
                      className={`badge ${
                        l.Status === "active"
                          ? "bg-emerald-100 text-emerald-700"
                          : l.Status === "closed"
                          ? "bg-gray-100 text-gray-700"
                          : l.Status === "defaulted"
                          ? "bg-red-100 text-red-700"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {l.Status}
                    </span>
                  </td>
                  <td className="flex gap-2">
                    <button
                      className="text-blue-600 text-xs inline-flex items-center gap-1"
                      onClick={() => setInterestLoanId(l.LoanID)}
                    >
                      <Calculator size={14} /> Interest
                    </button>
                    {hasRole("manager", "teller") && l.Status !== "closed" && (
                      <button
                        className="text-emerald-700 text-xs inline-flex items-center gap-1"
                        onClick={() => {
                          fPay.reset({ Amount: 0 });
                          setPayingLoan(l);
                        }}
                      >
                        <CreditCard size={14} /> Pay
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

      {/* New loan modal */}
      <Modal open={openForm} onClose={() => setOpenForm(false)} title="New loan">
        <form
          onSubmit={fNew.handleSubmit((d: any) => create.mutate(d))}
          className="space-y-3"
        >
          <div>
            <label className="label">CustomerID</label>
            <input className="input" type="number" {...fNew.register("CustomerID")} />
          </div>
          <div>
            <label className="label">Principal</label>
            <input className="input" type="number" step="0.01" {...fNew.register("Principal")} />
          </div>
          <div>
            <label className="label">Interest rate (annual %)</label>
            <input className="input" type="number" step="0.01" {...fNew.register("InterestRate")} />
          </div>
          <div>
            <label className="label">Term (months)</label>
            <input className="input" type="number" {...fNew.register("TermMonths")} />
          </div>
          <div>
            <label className="label">Start date</label>
            <input className="input" type="date" {...fNew.register("StartDate")} />
          </div>
          <button className="btn-primary w-full" disabled={create.isPending}>
            {create.isPending ? "Creating..." : "Create loan"}
          </button>
        </form>
      </Modal>

      {/* Payment modal */}
      <Modal
        open={!!payingLoan}
        onClose={() => setPayingLoan(null)}
        title={payingLoan ? `Pay loan #${payingLoan.LoanID}` : ""}
      >
        {payingLoan && (
          <form
            onSubmit={fPay.handleSubmit((d: any) =>
              pay.mutate({ id: payingLoan.LoanID, amount: d.Amount })
            )}
            className="space-y-3"
          >
            <div className="text-sm">
              <div>
                Outstanding:{" "}
                <b>{fmtMoney(payingLoan.Outstanding ?? payingLoan.Principal)}</b>
              </div>
            </div>
            <div>
              <label className="label">Payment amount</label>
              <input className="input" type="number" step="0.01" {...fPay.register("Amount")} />
            </div>
            <button className="btn-primary w-full" disabled={pay.isPending}>
              {pay.isPending ? "Processing..." : "Submit payment"}
            </button>
          </form>
        )}
      </Modal>

      <InterestModal id={interestLoanId} onClose={() => setInterestLoanId(null)} />
    </div>
  );
}

function InterestModal({
  id,
  onClose,
}: {
  id: number | null;
  onClose: () => void;
}) {
  const q = useQuery({
    queryKey: ["loan-interest", id],
    queryFn: () => loanService.interest(id as number),
    enabled: !!id,
  });
  const r: any = q.data;
  return (
    <Modal open={!!id} onClose={onClose} title="Loan interest details">
      {!r ? (
        <div className="text-sm text-ink/60">Computing...</div>
      ) : (
        <div className="space-y-2 text-sm">
          <div><b>Monthly payment:</b> {fmtMoney(r.MonthlyPayment)}</div>
          <div><b>Total payable:</b> {fmtMoney(r.TotalPayable)}</div>
          <div><b>Total interest:</b> {fmtMoney(r.TotalInterest)}</div>
          <div><b>Outstanding:</b> {fmtMoney(r.Outstanding)}</div>
          <div><b>Remaining interest (est.):</b> {fmtMoney(r.RemainingInterest)}</div>
        </div>
      )}
    </Modal>
  );
}
