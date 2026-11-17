import type { User } from "firebase/auth";

import { apiFetch } from "./api";

export type TransactionType = "income" | "expense";

export interface TransactionInput {
  date: string;
  type: TransactionType;
  amount_jpy: number;
  category: string;
  note: string | null;
}

export interface Transaction extends TransactionInput {
  transaction_id: string;
  created_at: string;
}

export function listTransactions(user: User, month: string): Promise<Transaction[]> {
  return apiFetch(user, `/api/transactions?month=${encodeURIComponent(month)}`);
}

export function createTransaction(user: User, input: TransactionInput): Promise<Transaction> {
  return apiFetch(user, "/api/transactions", { method: "POST", body: JSON.stringify(input) });
}

export function updateTransaction(user: User, id: string, input: TransactionInput): Promise<Transaction> {
  return apiFetch(user, `/api/transactions/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(input) });
}

export function deleteTransaction(user: User, id: string): Promise<void> {
  return apiFetch(user, `/api/transactions/${encodeURIComponent(id)}`, { method: "DELETE" });
}
