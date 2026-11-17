"use client";

import type { User } from "firebase/auth";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import { formatYen } from "@/lib/format";
import { getMonthlySummary, type MonthlySummary } from "@/lib/transactions";

/** 月次サマリー。合計と内訳は API が計算した値をそのまま表示する(A6)。棒の長さだけを画面で決める */
export default function Summary({ user, month, version }: { user: User; month: string; version: number }) {
  const [summary, setSummary] = useState<MonthlySummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getMonthlySummary(user)
      .then((data) => {
        if (cancelled) return;
        setSummary(data);
        setError(null);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof ApiError ? e.message : "サマリーの読み込みに失敗しました");
      });
    return () => {
      cancelled = true;
    };
  }, [user, version]);

  if (error) return <p className="error">{error}</p>;

  const current = summary.find((m) => m.month === month);
  if (!current) return <p>この月の取引はありません</p>;

  const max = Math.max(1, ...current.expense_by_category.map((c) => Math.abs(c.total)));

  return (
    <section className="summary">
      <dl>
        <dt>収入合計</dt>
        <dd className="num">{formatYen(current.income_total)}</dd>
        <dt>支出合計</dt>
        <dd className="num">{formatYen(current.expense_total)}</dd>
      </dl>
      <h3>支出のカテゴリ別内訳</h3>
      <ul className="bars">
        {current.expense_by_category.map((c) => (
          <li key={c.category}>
            <span className="bar-label">{c.category}</span>
            <span className="bar" style={{ width: `${(Math.abs(c.total) / max) * 100}%` }} />
            <span className="num">{formatYen(c.total)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
