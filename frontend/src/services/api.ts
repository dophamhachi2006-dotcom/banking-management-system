import axios from "axios";
import { toast } from "sonner";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:5000/api",
  timeout: 15_000,
});

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("bms_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err?.response?.data?.message || err.message || "Network error";
    if (err?.response?.status === 401) {
      localStorage.removeItem("bms_token");
      localStorage.removeItem("bms_user");
      if (location.pathname !== "/login") location.href = "/login";
    } else {
      toast.error(msg);
    }
    return Promise.reject(err);
  },
);

export const unwrap = <T,>(p: Promise<{ data: { data: T } }>) =>
  p.then((r) => r.data.data);
