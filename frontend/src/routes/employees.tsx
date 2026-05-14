import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { employeeService } from "@/services";
import { employeeSchema } from "@/lib/validations";
import { Modal } from "@/components/Modal";
import { Pagination } from "@/components/Pagination";
import { SkeletonTable } from "@/components/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { fmtMoney } from "@/lib/utils";
import { Plus, Pencil, Trash2, Search } from "lucide-react";
import { useFilters } from "@/hooks/useFilters";
import { FilterBar, type FieldDef } from "@/components/FilterBar";

export function EmployeesPage() {
  const { hasRole } = useAuth();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [openForm, setOpenForm] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);

  const { filters, setFilter, removeFilter, clear, sort, setSort, queryParams } = useFilters();
  const list = useQuery({
    queryKey: ["employees", page, q, queryParams],
    queryFn: () => employeeService.list({ page, size: 20, q, ...queryParams }),
  });
  const fields: FieldDef[] = [
    { field: "Salary", label: "Salary", type: "numeric" },
    { field: "Status", label: "Status", type: "enum",
      options: [{label:"active",value:"active"},{label:"inactive",value:"inactive"}] },
  ];
  const sortOptions = [
    { label: "Salary ↑", value: "Salary_asc" },
    { label: "Salary ↓", value: "Salary_desc" },
  ];
  const create = useMutation({
    mutationFn: (d: any) => employeeService.create(d),
    onSuccess: () => {
      toast.success("Created");
      setOpenForm(false);
      qc.invalidateQueries({ queryKey: ["employees"] });
    },
  });
  const update = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      employeeService.update(id, data),
    onSuccess: () => {
      toast.success("Updated");
      setOpenForm(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["employees"] });
    },
  });
  const del = useMutation({
    mutationFn: (id: number) => employeeService.remove(id),
    onSuccess: () => {
      toast.success("Deleted");
      qc.invalidateQueries({ queryKey: ["employees"] });
    },
  });

  const f = useForm({ resolver: zodResolver(employeeSchema) });

  const openCreate = () => {
    setEditing(null);
    f.reset({
      FullName: "",
      Email: "",
      Phone: "",
      Position: "",
      BranchID: undefined,
      Salary: 0,
      Status: "active",
    });
    setOpenForm(true);
  };
  const openEdit = (e: any) => {
    setEditing(e);
    f.reset({
      FullName: e.FullName,
      Email: e.Email,
      Phone: e.Phone ?? "",
      Position: e.Position ?? "",
      BranchID: e.BranchID,
      Salary: e.Salary ?? 0,
      Status: e.Status ?? "active",
    });
    setOpenForm(true);
  };
  const onSubmit = (d: any) => {
    if (editing) update.mutate({ id: editing.EmployeeID, data: d });
    else create.mutate(d);
  };

  const items: any[] = (list.data as any)?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="font-display text-3xl">Employees</h1>
        {hasRole("manager") && (
          <button className="btn-primary" onClick={openCreate}>
            <Plus size={16} /> New employee
          </button>
        )}
      </div>
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <Search size={16} className="text-ink/40" />
          <input
            className="input"
            placeholder="Search by ID, name, email, position, branch..."
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
                <th>ID</th><th>Name</th><th>Email</th><th>Position</th>
                <th>Branch</th><th>Salary</th><th>Status</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((e) => (
                <tr key={e.EmployeeID}>
                  <td>{e.EmployeeID}</td>
                  <td>{e.FullName}</td>
                  <td>{e.Email}</td>
                  <td>{e.Position}</td>
                  <td>{e.BranchName}</td>
                  <td>{fmtMoney(e.Salary ?? 0)}</td>
                  <td>{e.Status}</td>
                  <td className="flex gap-2">
                    {hasRole("manager") && (
                      <>
                        <button
                          className="text-amber-700 text-xs inline-flex items-center gap-1"
                          onClick={() => openEdit(e)}
                        >
                          <Pencil size={14} /> Edit
                        </button>
                        <button
                          className="text-red-600 text-xs inline-flex items-center gap-1"
                          onClick={() =>
                            confirm(`Delete employee #${e.EmployeeID}?`) &&
                            del.mutate(e.EmployeeID)
                          }
                        >
                          <Trash2 size={14} /> Delete
                        </button>
                      </>
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

      <Modal
        open={openForm}
        onClose={() => {
          setOpenForm(false);
          setEditing(null);
        }}
        title={editing ? `Edit employee #${editing.EmployeeID}` : "New employee"}
      >
        <form onSubmit={f.handleSubmit(onSubmit)} className="space-y-3">
          {(["FullName", "Email", "Phone", "Position"] as const).map((k) => (
            <div key={k}>
              <label className="label">{k}</label>
              <input className="input" {...f.register(k)} />
            </div>
          ))}
          <div>
            <label className="label">BranchID</label>
            <input className="input" type="number" {...f.register("BranchID")} />
          </div>
          <div>
            <label className="label">Salary</label>
            <input className="input" type="number" step="0.01" {...f.register("Salary")} />
          </div>
          <div>
            <label className="label">Status</label>
            <select className="input" {...f.register("Status")}>
              <option value="active">active</option>
              <option value="inactive">inactive</option>
            </select>
          </div>
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
    </div>
  );
}
