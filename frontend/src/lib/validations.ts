import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().min(3, "Tối thiểu 3 ký tự").max(60),
  password: z.string().min(6, "Tối thiểu 6 ký tự").max(100),
});

/**
 * Customer schema.
 *
 * IMPORTANT: We intentionally do NOT include `CustomerID` here.
 * CustomerID is assigned by the database (AUTO_INCREMENT) and must never be
 * sent by the client. This prevents the "numeric input auto-added to ID" bug
 * reported in feedback.
 */
export const customerSchema = z.object({
  FullName: z.string().trim().min(1, "Bắt buộc").max(120),
  Email: z.string().email("Email không hợp lệ").max(120).optional().or(z.literal("")),
  Phone: z.string().max(20).optional().or(z.literal("")),
  DateOfBirth: z.string().optional().or(z.literal("")),
  Address: z.string().max(255).optional().or(z.literal("")),
  City: z.string().max(80).optional().or(z.literal("")),
  IDNumber: z.string().max(30).optional().or(z.literal("")),
});

export const accountSchema = z.object({
  CustomerID: z.coerce.number().int().positive(),
  BranchID: z.coerce.number().int().positive(),
  AccountType: z.enum(["savings", "checking", "fixed"]).default("savings"),
  Balance: z.coerce.number().min(0).default(0),
  Currency: z.string().max(5).default("USD"),
});

export const txAmountSchema = z.object({
  AccountID: z.coerce.number().int().positive(),
  Amount: z.coerce.number().positive().max(10_000_000),
  Description: z.string().max(255).optional(),
});

export const transferSchema = z.object({
  FromAccountID: z.coerce.number().int().positive(),
  ToAccountID: z.coerce.number().int().positive(),
  Amount: z.coerce.number().positive().max(10_000_000),
  Description: z.string().max(255).optional(),
}).refine((d) => d.FromAccountID !== d.ToAccountID, {
  message: "Hai tài khoản phải khác nhau", path: ["ToAccountID"],
});

export const loanSchema = z.object({
  CustomerID: z.coerce.number().int().positive(),
  Principal: z.coerce.number().positive(),
  InterestRate: z.coerce.number().min(0).max(100),
  TermMonths: z.coerce.number().int().positive().max(600),
  StartDate: z.string().optional().or(z.literal("")),
});

export const loanPaymentSchema = z.object({
  Amount: z.coerce.number().positive(),
});

export const cardSchema = z.object({
  CustomerID: z.coerce.number().int().positive(),
  CreditLimit: z.coerce.number().positive(),
  ExpiryDate: z.string().optional().or(z.literal("")),
  CardNumber: z.string().max(20).optional().or(z.literal("")),
});

export const employeeSchema = z.object({
  FullName: z.string().trim().min(1).max(120),
  Email: z.string().email().max(120),
  Phone: z.string().max(20).optional().or(z.literal("")),
  Position: z.string().max(80).optional().or(z.literal("")),
  BranchID: z.coerce.number().int().positive().optional(),
  Salary: z.coerce.number().min(0).optional(),
  Status: z.enum(["active", "inactive"]).default("active"),
});
