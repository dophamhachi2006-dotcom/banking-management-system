import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { routeTree } from "./routeTree";
import { AuthProvider } from "./contexts/AuthContext";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

const router = createRouter({ routeTree, defaultPreloadStaleTime: 0 });
declare module "@tanstack/react-router" {
  interface Register { router: typeof router }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
        <Toaster richColors position="top-right" />
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);

