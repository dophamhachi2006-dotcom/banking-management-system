import { api, unwrap } from "./api";
export const authService = {
  login: (username: string, password: string) =>
    unwrap(api.post("/auth/login", { username, password })),
  me: () => unwrap(api.get("/auth/me")),
  logout: () => api.post("/auth/logout"),
};
