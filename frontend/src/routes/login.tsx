import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";
import { loginSchema } from "@/lib/validations";
import { useAuth } from "@/contexts/AuthContext";
import { ShieldAlert } from "lucide-react";

export function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const f = useForm({ resolver: zodResolver(loginSchema) });
  const onSubmit = async (d: any) => {
    try { await login(d.username, d.password); toast.success("Welcome!"); nav({ to: "/" }); }
    catch (e: any) { toast.error(e?.response?.data?.message || "Login failed"); }
  };
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-dark via-primary to-primary-dark p-4">
      <form onSubmit={f.handleSubmit(onSubmit)} className="card w-full max-w-md shadow-elegant">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
            <ShieldAlert/>
          </div>
          <div>
            <h1 className="font-display text-2xl">Emerald Bank</h1>
            <p className="text-sm text-ink/60">Management Console</p>
          </div>
        </div>
        <label className="label">Username</label>
        <input className="input" {...f.register("username")} />
        {f.formState.errors.username && <p className="text-xs text-red-600 mt-1">{f.formState.errors.username.message as string}</p>}
        <label className="label mt-4">Password</label>
        <input className="input" type="password" {...f.register("password")} />
        {f.formState.errors.password && <p className="text-xs text-red-600 mt-1">{f.formState.errors.password.message as string}</p>}
        <button disabled={f.formState.isSubmitting} className="btn-primary w-full mt-6">
          {f.formState.isSubmitting ? "Signing in..." : "Sign in"}
        </button>
        <p className="text-xs text-ink/50 mt-4 text-center">
          Default: admin/admin123 · teller1/teller123 · audit1/audit123
        </p>
      </form>
    </div>
  );
}
