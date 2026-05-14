import { api, unwrap } from "./api";

export interface PageParams { page?: number; size?: number; q?: string }
export interface Paged<T> { items: T[]; total: number; page: number; size: number }

const crud = <T>(base: string) => ({
  list: (p: PageParams & Record<string, any> = {}) =>
    unwrap<Paged<T>>(api.get(base, { params: p })),
  get: (id: number) => unwrap<T>(api.get(`${base}/${id}`)),
  create: (data: Partial<T>) => unwrap<{ id: number }>(api.post(base, data)),
  update: (id: number, data: Partial<T>) =>
    unwrap(api.put(`${base}/${id}`, data)),
  remove: (id: number) => unwrap(api.delete(`${base}/${id}`)),
});

export const customerService = crud<any>("/customers");
export const employeeService = crud<any>("/employees");
export const branchService = crud<any>("/branches");

export const accountService = {
  ...crud<any>("/accounts"),
  balance: (id: number) => unwrap(api.get(`/accounts/${id}/balance`)),
  setStatus: (id: number, status: "active" | "frozen" | "closed") =>
    unwrap(api.put(`/accounts/${id}/status`, { Status: status })),
};

export const loanService = {
  ...crud<any>("/loans"),
  pay: (id: number, amount: number) =>
    unwrap(api.post(`/loans/${id}/payment`, { Amount: amount })),
  interest: (id: number) => unwrap(api.get(`/loans/${id}/interest`)),
  setStatus: (id: number, status: string) =>
    unwrap(api.put(`/loans/${id}/status`, { Status: status })),
};

export const cardService = {
  ...crud<any>("/cards"),
  transactions: (id: number) => unwrap(api.get(`/cards/${id}/transactions`)),
  setStatus: (id: number, status: "active" | "blocked" | "expired") =>
    unwrap(api.put(`/cards/${id}/status`, { Status: status })),
};

export const transactionService = {
  list: (params: Record<string, any> = {}) =>
    unwrap<Paged<any>>(api.get("/transactions", { params })),
  deposit: (d: any) => unwrap(api.post("/transactions/deposit", d)),
  withdraw: (d: any) => unwrap(api.post("/transactions/withdraw", d)),
  transfer: (d: any) => unwrap(api.post("/transactions/transfer", d)),
  fraudCheck: (accountId: number) =>
    unwrap(api.get(`/transactions/fraud/${accountId}`)),
};

export const reportService = {
  dashboard: () => unwrap(api.get("/reports/dashboard")),
  topCustomers: (limit = 10) =>
    unwrap(api.get("/reports/top-customers", { params: { limit } })),
  branchPerf: () => unwrap(api.get("/reports/branch-performance")),
  monthly: () => unwrap(api.get("/reports/monthly-summary")),
  revenue: (months = 12) =>
    unwrap(api.get("/reports/revenue", { params: { months } })),
  txBreakdown: () => unwrap(api.get("/reports/tx-breakdown")),
  fraud: () => unwrap(api.get("/reports/fraud")),
  suspicious: (params: Record<string, any> = {}) =>
    unwrap(api.get("/reports/suspicious", { params })),
};

export const auditService = {
  list: (params: any = {}) =>
    unwrap<Paged<any>>(api.get("/audit", { params })),
  summary: () => unwrap(api.get("/audit/summary")),
};
