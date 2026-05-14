import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { branchService } from "@/services";
import { Modal } from "@/components/Modal";
import { Pagination } from "@/components/Pagination";
import { SkeletonTable } from "@/components/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { Plus, Pencil, Trash2, Search } from "lucide-react";
import { useFilters } from "@/hooks/useFilters";
import { FilterBar, type FieldDef } from "@/components/FilterBar";

type Branch = {
  BranchID: number;
  BranchName: string;
  Address?: string;
  City?: string;
  Phone?: string;
  ManagerID?: number;
  ManagerName?: string;
};

export function BranchesPage() {
  const { hasRole } = useAuth();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [openForm, setOpenForm] = useState(false);
  const [editing, setEditing] = useState<Branch | null>(null);

  const { filters, setFilter, removeFilter, clear, sort, setSort, queryParams } = useFilters();
  const list = useQuery({
    queryKey: ["branches", page, q, queryParams],
    queryFn: () => branchService.list({ page, size: 20, q, ...queryParams }),
  });
  const fields: FieldDef[] = [
    { field: "HasManager", label: "Has manager", type: "bool" },
  ];
  const sortOptions: { label: string; value: string }[] = [];

  const create = useMutation({
    mutationFn: (d: any) => branchService.create(d),
    onSuccess: () => {
      toast.success("Branch created");
      setOpenForm(false);
      qc.invalidateQueries({ queryKey: ["branches"] });
    },
  });
  const update = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      branchService.update(id, data),
    onSuccess: () => {
      toast.success("Branch updated");
      setOpenForm(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["branches"] });
    },
  });
  const del = useMutation({
    mutationFn: (id: number) => branchService.remove(id),
    onSuccess: () => {
      toast.success("Deleted");
      qc.invalidateQueries({ queryKey: ["branches"] });
    },
  });

  const f = useForm<any>();

  const openCreate = () => {
    setEditing(null);
    f.reset({
      BranchName: "",
      Address: "",
      City: "",
      Phone: "",
      ManagerID: "",
    });
    setOpenForm(true);
  };
  const openEdit = (b: Branch) => {
    setEditing(b);
    f.reset({
      BranchName: b.BranchName || "",
      Address: b.Address || "",
      City: b.City || "",
      Phone: b.Phone || "",
      ManagerID: b.ManagerID ?? "",
    });
    setOpenForm(true);
  };
  const onSubmit = (d: any) => {
    const payload: any = {
      BranchName: d.BranchName,
      Address: d.Address || null,
      City: d.City || null,
      Phone: d.Phone || null,
    };
    if (d.ManagerID !== "" && d.ManagerID != null) {
      payload.ManagerID = Number(d.ManagerID);
    }
    if (editing) update.mutate({ id: editing.BranchID, data: payload });
    else create.mutate(payload);
  };

  const items: Branch[] = ((list.data as any)?.items ?? []) as Branch[];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="font-display text-3xl">Branches</h1>
        {hasRole("manager") && (
          <button className="btn-primary" onClick={openCreate}>
            <Plus size={16} /> New branch
          </button>
        )}
      </div>
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <Search size={16} className="text-ink/40" />
          <input
            className="input"
            placeholder="Search by ID, name, city, phone or manager..."
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
                <th>ID</th><th>Name</th><th>City</th>
                <th>Phone</th><th>Manager</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((b) => (
                <tr key={b.BranchID}>
                  <td>{b.BranchID}</td>
                  <td>{b.BranchName}</td>
                  <td>{b.City}</td>
                  <td>{b.Phone}</td>
                  <td>{b.ManagerName ?? "—"}</td>
                  <td className="flex gap-2">
                    {hasRole("manager") && (
                      <>
                        <button
                          className="text-amber-700 text-xs inline-flex items-center gap-1"
                          onClick={() => openEdit(b)}
                        >
                          <Pencil size={14} /> Edit
                        </button>
                        <button
                          className="text-red-600 text-xs inline-flex items-center gap-1"
                          onClick={() =>
                            confirm(`Delete branch #${b.BranchID}?`) &&
                            del.mutate(b.BranchID)
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
        title={editing ? `Edit branch #${editing.BranchID}` : "New branch"}
      >
        <form onSubmit={f.handleSubmit(onSubmit)} className="space-y-3">
          <div>
            <label className="label">BranchName *</label>
            <input
              className="input"
              {...f.register("BranchName", { required: true })}
            />
          </div>
          <div>
            <label className="label">Address</label>
            <input className="input" {...f.register("Address")} />
          </div>
          <div>
            <label className="label">City</label>
            <input className="input" {...f.register("City")} />
          </div>
          <div>
            <label className="label">Phone</label>
            <input className="input" {...f.register("Phone")} />
          </div>
          <div>
            <label className="label">ManagerID (optional)</label>
            <input
              className="input"
              type="number"
              {...f.register("ManagerID")}
            />
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
