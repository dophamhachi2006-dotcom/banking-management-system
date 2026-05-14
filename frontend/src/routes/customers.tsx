import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { customerService } from "@/services";
import { customerSchema } from "@/lib/validations";
import { Modal } from "@/components/Modal";
import { Pagination } from "@/components/Pagination";
import { SkeletonTable } from "@/components/Skeleton";
import { fmtMoney, fmtDate } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { Plus, Search, Eye, Pencil, Trash2 } from "lucide-react";
import { useFilters } from "@/hooks/useFilters";
import { FilterBar, type FieldDef } from "@/components/FilterBar";

type Customer = {
  CustomerID: number;
  FullName: string;
  Email?: string;
  Phone?: string;
  DateOfBirth?: string;
  Address?: string;
  City?: string;
  IDNumber?: string;
  AccountCount?: number;
  TotalBalance?: number;
};

export function CustomersPage() {
  const { hasRole } = useAuth();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [viewingId, setViewingId] = useState<number | null>(null);

  const { filters, setFilter, removeFilter, clear, sort, setSort, queryParams } = useFilters();

  const list = useQuery({
    queryKey: ["customers", page, q, queryParams],
    queryFn: () => customerService.list({ page, size: 20, q, ...queryParams }),
  });

  const fields: FieldDef[] = [
    { field: "TotalBalance", label: "Total Balance", type: "numeric" },
    { field: "AccountCount", label: "Accounts", type: "numeric", operators: ["gt", "lt", "eq"] },
    { field: "City", label: "City", type: "string" },
    { field: "FullName", label: "Name", type: "string" },
  ];

  const sortOptions = [
    { label: "Total Balance ↑", value: "TotalBalance_asc" },
    { label: "Total Balance ↓", value: "TotalBalance_desc" },
    { label: "Accounts ↑", value: "AccountCount_asc" },
    { label: "Accounts ↓", value: "AccountCount_desc" },
    { label: "Created ↓", value: "CreatedAt_desc" },
  ];

  const create = useMutation({
    mutationFn: (d: any) => customerService.create(d),
    onSuccess: () => {
      toast.success("Customer created");
      setFormOpen(false);
      qc.invalidateQueries({ queryKey: ["customers"] });
    },
  });

  const update = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      customerService.update(id, data),
    onSuccess: () => {
      toast.success("Customer updated");
      setFormOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["customers"] });
    },
  });

  const del = useMutation({
    mutationFn: (id: number) => customerService.remove(id),
    onSuccess: () => {
      toast.success("Deleted");
      qc.invalidateQueries({ queryKey: ["customers"] });
    },
  });

  const f = useForm({ resolver: zodResolver(customerSchema) });

  const openCreate = () => {
    setEditing(null);
    f.reset({
      FullName: "",
      Email: "",
      Phone: "",
      DateOfBirth: "",
      Address: "",
      City: "",
      IDNumber: "",
    });
    setFormOpen(true);
  };

  const openEdit = (c: Customer) => {
    setEditing(c);
    f.reset({
      FullName: c.FullName || "",
      Email: c.Email || "",
      Phone: c.Phone || "",
      DateOfBirth: c.DateOfBirth ? c.DateOfBirth.slice(0, 10) : "",
      Address: c.Address || "",
      City: c.City || "",
      IDNumber: c.IDNumber || "",
    });
    setFormOpen(true);
  };

  const onSubmit = (d: any) => {
    // Never send CustomerID — DB auto-assigns; fixes "number added to ID" bug
    delete d.CustomerID;
    if (editing) update.mutate({ id: editing.CustomerID, data: d });
    else create.mutate(d);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="font-display text-3xl">Customers</h1>
        {hasRole("manager", "teller") && (
          <button className="btn-primary" onClick={openCreate}>
            <Plus size={16} /> New customer
          </button>
        )}
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <Search size={16} className="text-ink/40" />
          <input
            className="input"
            placeholder="Search by ID, name, email, phone, IDNumber..."
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
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>City</th>
                <th>Accounts</th>
                <th>Total Balance</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(list.data as any)?.items?.map((c: Customer) => (
                <tr key={c.CustomerID}>
                  <td>{c.CustomerID}</td>
                  <td>{c.FullName}</td>
                  <td>{c.Email}</td>
                  <td>{c.Phone}</td>
                  <td>{c.City}</td>
                  <td>{c.AccountCount ?? 0}</td>
                  <td>{fmtMoney(c.TotalBalance ?? 0)}</td>
                  <td className="flex gap-2">
                    <button
                      className="text-blue-600 text-xs inline-flex items-center gap-1"
                      onClick={() => setViewingId(c.CustomerID)}
                      title="View detail"
                    >
                      <Eye size={14} /> View
                    </button>
                    {hasRole("manager", "teller") && (
                      <button
                        className="text-amber-700 text-xs inline-flex items-center gap-1"
                        onClick={() => openEdit(c)}
                        title="Edit"
                      >
                        <Pencil size={14} /> Edit
                      </button>
                    )}
                    {hasRole("manager") && (
                      <button
                        className="text-red-600 text-xs inline-flex items-center gap-1"
                        onClick={() =>
                          confirm(`Delete customer #${c.CustomerID}?`) &&
                          del.mutate(c.CustomerID)
                        }
                        title="Delete"
                      >
                        <Trash2 size={14} /> Delete
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

      {/* Create / Edit modal */}
      <Modal
        open={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditing(null);
        }}
        title={editing ? `Edit customer #${editing.CustomerID}` : "New customer"}
      >
        <form onSubmit={f.handleSubmit(onSubmit)} className="space-y-3">
          {(
            ["FullName", "Email", "Phone", "DateOfBirth", "Address", "City", "IDNumber"] as const
          ).map((k) => (
            <div key={k}>
              <label className="label">{k}</label>
              <input
                className="input"
                {...f.register(k)}
                type={k === "DateOfBirth" ? "date" : "text"}
                placeholder={k === "IDNumber" ? "National ID (free text)" : undefined}
              />
              {f.formState.errors[k] && (
                <p className="text-xs text-red-600">
                  {f.formState.errors[k]?.message as string}
                </p>
              )}
            </div>
          ))}
          <button
            className="btn-primary w-full"
            disabled={create.isPending || update.isPending}
          >
            {create.isPending || update.isPending
              ? "Saving..."
              : editing
              ? "Update"
              : "Create"}
          </button>
        </form>
      </Modal>

      {/* View detail modal */}
      <CustomerDetailModal
        id={viewingId}
        onClose={() => setViewingId(null)}
      />
    </div>
  );
}

function CustomerDetailModal({
  id,
  onClose,
}: {
  id: number | null;
  onClose: () => void;
}) {
  const q = useQuery({
    queryKey: ["customer", id],
    queryFn: () => customerService.get(id as number),
    enabled: !!id,
  });
  const c: any = q.data;
  return (
    <Modal open={!!id} onClose={onClose} title={c ? `Customer #${c.CustomerID}` : "Loading..."}>
      {!c ? (
        <div className="text-sm text-ink/60">Loading...</div>
      ) : (
        <div className="space-y-4 text-sm">
          <div className="grid grid-cols-2 gap-2">
            <div><b>Name:</b> {c.FullName}</div>
            <div><b>Email:</b> {c.Email || "—"}</div>
            <div><b>Phone:</b> {c.Phone || "—"}</div>
            <div><b>DOB:</b> {c.DateOfBirth ? fmtDate(c.DateOfBirth) : "—"}</div>
            <div className="col-span-2"><b>Address:</b> {c.Address || "—"} ({c.City || "—"})</div>
            <div><b>IDNumber:</b> {c.IDNumber || "—"}</div>
          </div>

          <div>
            <h4 className="font-semibold mt-3 mb-1">Accounts ({c.accounts?.length ?? 0})</h4>
            <table className="table-base text-xs">
              <thead>
                <tr><th>ID</th><th>Number</th><th>Branch</th><th>Type</th><th>Balance</th><th>Status</th></tr>
              </thead>
              <tbody>
                {c.accounts?.map((a: any) => (
                  <tr key={a.AccountID}>
                    <td>{a.AccountID}</td>
                    <td>{a.AccountNumber}</td>
                    <td>{a.BranchName}</td>
                    <td>{a.AccountType}</td>
                    <td>{fmtMoney(a.Balance ?? 0)}</td>
                    <td>{a.Status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h4 className="font-semibold mt-3 mb-1">
              Recent transactions ({c.recent_transactions?.length ?? 0})
            </h4>
            <table className="table-base text-xs">
              <thead>
                <tr><th>When</th><th>Account</th><th>Type</th><th>Amount</th></tr>
              </thead>
              <tbody>
                {c.recent_transactions?.slice(0, 10).map((t: any) => (
                  <tr key={t.TransactionID}>
                    <td>{fmtDate(t.CreatedAt)}</td>
                    <td>{t.AccountNumber}</td>
                    <td>{t.TxType}</td>
                    <td>{fmtMoney(t.Amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Modal>
  );
}
