import { ReactNode } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Navigate } from "@tanstack/react-router";

export function Protected({ children, roles }: { children: ReactNode; roles?: string[] }) {
  const { user, hasRole } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.some((r) => hasRole(r as any))) {
    return <div className="card text-center text-red-600">403 — Forbidden</div>;
  }
  return <>{children}</>;
}
