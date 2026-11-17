"use client";

import type { User } from "firebase/auth";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import { currentMonth, formatYen } from "@/lib/format";
import {
  createTransaction,
  deleteTransaction,
  listTransactions,
  type Transaction,
  type TransactionInput,
} from "@/lib/transactions";

import TransactionForm from "./TransactionForm";

const TYPE_LABEL = { income: "収入", expense: "支出" } as const;

export default function Transactions({ user }: { user: User }) {
  const [month, setMonth] = useState(currentMonth());
  const [rows, setRows] = useState<Transaction[]>([]);
  const [error, setError] = useState<string | null>(null);

  // 登録・削除のたびに数を増やし、一覧を読み直す
  const [version, setVersion] = useState(0);
  const reload = () => setVersion((v) => v + 1);

  useEffect(() => {
    let cancelled = false;
    listTransactions(user, month)
      .then((data) => {
        if (cancelled) return;
        setRows(data);
        setError(null);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof ApiError ? e.message : "読み込みに失敗しました");
      });
    return () => {
      cancelled = true;
    };
  }, [user, month, version]);

  async function add(input: TransactionInput) {
    try {
      await createTransaction(user, input);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "登録に失敗しました");
      throw e; // フォームの入力を消さないため
    }
  }

  async function remove(id: string) {
    if (!window.confirm("この取引を削除しますか?")) return;
    try {
      await deleteTransaction(user, id);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "削除に失敗しました");
    }
  }

  return (
    <section>
      <TransactionForm onSubmit={add} />
      {error && <p className="error">{error}</p>}
      <label>
        月: <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
      </label>
      <table>
        <thead>
          <tr>
            <th>日付</th>
            <th>種別</th>
            <th>金額</th>
            <th>カテゴリ</th>
            <th>メモ</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.transaction_id}>
              <td>{t.date}</td>
              <td>{TYPE_LABEL[t.type]}</td>
              <td className="num">{formatYen(t.amount_jpy)}</td>
              <td>{t.category}</td>
              <td>{t.note}</td>
              <td>
                <button onClick={() => remove(t.transaction_id)}>削除</button>
              </td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={6}>この月の取引はありません</td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
