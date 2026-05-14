import { ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
export const cn = (...xs: ClassValue[]) => twMerge(clsx(xs));

export const fmtMoney = (n: number | string, ccy = "USD") =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: ccy,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(typeof n === "string" ? parseFloat(n) : n);

export const fmtMoneyCompact = (n: number | string, ccy = "USD") =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: ccy,
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(typeof n === "string" ? parseFloat(n) : n);

export const fmtCompact = (n: number) =>
  new Intl.NumberFormat("en", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(n);

export const fmtMonth = (m: string) =>
  m && /^\d{4}-\d{2}$/.test(m)
    ? new Date(m + "-01").toLocaleDateString("en-US", {
        month: "short",
        year: "2-digit",
      })
    : m;

export const fmtDate = (s: string | Date) => new Date(s).toLocaleString();
