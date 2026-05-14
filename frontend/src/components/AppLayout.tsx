import { Link, Outlet, useRouterState, useNavigate } from "@tanstack/react-router";
import {
  LayoutDashboard, Users, CreditCard, ArrowLeftRight, Building2,
  UserCog, FileBarChart2, ScrollText, Wallet, ShieldAlert, LogOut, Menu, X
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useState } from "react";
import { cn } from "@/lib/utils";

type Role = "manager" | "teller" | "auditor";
const NAV: { to: string; label: string; icon: any; roles?: Role[] }[] = [
  { to: "/",             label: "Dashboard",   icon: LayoutDashboard },
  { to: "/customers",    label: "Customers",   icon: Users },
  { to: "/accounts",     label: "Accounts",    icon: CreditCard },
  { to: "/transactions", label: "Transactions",icon: ArrowLeftRight },
  { to: "/loans",        label: "Loans",       icon: Wallet },
  { to: "/cards",        label: "Credit Cards",icon: CreditCard },
  { to: "/employees",    label: "Employees",   icon: UserCog,   roles: ["manager"] },
  { to: "/branches",     label: "Branches",    icon: Building2 },
  { to: "/reports",      label: "Reports",     icon: FileBarChart2 },
  { to: "/audit",        label: "Audit Log",   icon: ScrollText, roles: ["manager","auditor"] },
];

export function AppLayout() {
  const { user, logout, hasRole } = useAuth();
  const nav = useNavigate();
  const path = useRouterState({ select: (s) => s.location.pathname });
  const [open, setOpen] = useState(false);

  if (!user) { nav({ to: "/login" }); return null; }

  return (
    <div className="min-h-screen flex">
      <aside className={cn(
        "fixed inset-y-0 left-0 z-30 w-64 bg-primary-dark text-white flex flex-col transition-transform",
        open ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      )}>
        <div className="px-5 py-5 border-b border-white/10 flex items-center gap-2">
          <ShieldAlert className="text-accent" />
          <div>
            <div className="font-display text-xl">Emerald Bank</div>
            <div className="text-xs text-white/60">Management Console</div>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-3">
          {NAV.filter(n => !n.roles || n.roles.some((r) => hasRole(r))).map((n) => {
            const Icon = n.icon;
            const active = path === n.to;
            return (
              <Link key={n.to} to={n.to} onClick={() => setOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-5 py-2.5 text-sm transition",
                  active ? "bg-accent/15 border-l-4 border-accent text-accent font-medium"
                         : "text-white/80 hover:bg-white/5"
                )}>
                <Icon size={18} /> {n.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-white/10">
          <div className="text-sm">{user.username}</div>
          <div className="text-xs text-accent capitalize">{user.role}</div>
          <button onClick={logout} className="mt-3 w-full btn-ghost text-white/80 hover:bg-white/10 text-sm">
            <LogOut size={16}/> Logout
          </button>
        </div>
      </aside>

      <div className="flex-1 md:ml-64">
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-white border-b">
          <button onClick={() => setOpen(o=>!o)}>{open ? <X/> : <Menu/>}</button>
          <span className="font-display text-lg">Emerald Bank</span>
          <span className="w-6"/>
        </header>
        <main className="p-6"><Outlet/></main>
      </div>
    </div>
  );
}
