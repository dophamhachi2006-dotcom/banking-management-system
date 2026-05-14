import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { authService } from "@/services/authService";

interface User { id: number; username: string; role: "manager"|"teller"|"auditor" }
interface Ctx {
  user: User | null;
  login: (u: string, p: string) => Promise<void>;
  logout: () => void;
  hasRole: (...rs: User["role"][]) => boolean;
}

const AuthCtx = createContext<Ctx>(null!);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem("bms_user");
    return raw ? JSON.parse(raw) : null;
  });

  useEffect(() => {
    if (user) localStorage.setItem("bms_user", JSON.stringify(user));
    else      localStorage.removeItem("bms_user");
  }, [user]);

  const login = async (username: string, password: string) => {
    const res: any = await authService.login(username, password);
    localStorage.setItem("bms_token", res.token);
    setUser(res.user);
  };
  const logout = () => {
    authService.logout().catch(() => {});
    localStorage.removeItem("bms_token");
    setUser(null);
  };
  const hasRole = (...rs: User["role"][]) => !!user && rs.includes(user.role);

  return <AuthCtx.Provider value={{ user, login, logout, hasRole }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
