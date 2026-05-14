import { createRootRoute, createRoute, Outlet, redirect } from "@tanstack/react-router";
import { AppLayout } from "@/components/AppLayout";
import { LoginPage } from "@/routes/login";
import { DashboardPage } from "@/routes/dashboard";
import { CustomersPage } from "@/routes/customers";
import { AccountsPage } from "@/routes/accounts";
import { TransactionsPage } from "@/routes/transactions";
import { LoansPage } from "@/routes/loans";
import { CardsPage } from "@/routes/cards";
import { EmployeesPage } from "@/routes/employees";
import { BranchesPage } from "@/routes/branches";
import { ReportsPage } from "@/routes/reports";
import { AdvancedReportsPage } from "@/routes/reports.advanced";
import { AuditPage } from "@/routes/audit";

const rootRoute = createRootRoute({ component: () => <Outlet /> });

const requireAuth = () => {
  if (!localStorage.getItem("bms_token")) throw redirect({ to: "/login" });
};

const loginRoute = createRoute({ getParentRoute: () => rootRoute, path: "/login", component: LoginPage });

const appRoute = createRoute({
  getParentRoute: () => rootRoute, id: "app",
  beforeLoad: requireAuth, component: AppLayout,
});

const mk = (path: string, Comp: any) =>
  createRoute({ getParentRoute: () => appRoute, path, component: Comp });

export const routeTree = rootRoute.addChildren([
  loginRoute,
  appRoute.addChildren([
    mk("/", DashboardPage),
    mk("/customers", CustomersPage),
    mk("/accounts", AccountsPage),
    mk("/transactions", TransactionsPage),
    mk("/loans", LoansPage),
    mk("/cards", CardsPage),
    mk("/employees", EmployeesPage),
    mk("/branches", BranchesPage),
    mk("/reports", ReportsPage),
    mk("/reports/advanced", AdvancedReportsPage),
    mk("/audit", AuditPage),
  ]),
]);
