"use client";

import { useState, type FormEvent } from "react";

import { today } from "@/lib/format";
import type { TransactionInput, TransactionType } from "@/lib/transactions";

interface Props {
  onSubmit: (input: TransactionInput) => Promise<void>;
}

export default function TransactionForm({ onSubmit }: Props) {
  const [date, setDate] = useState(today());
  const [type, setType] = useState<TransactionType>("expense");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      // 金額の検証は API が行う(A5)。ここでは数値に変換するだけ
      await onSubmit({ date, type, amount_jpy: Number(amount), category, note: note || null });
      setAmount("");
      setNote("");
    } catch {
      // エラーの表示は呼び出し側が行う。入力は残す
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="form">
      <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required aria-label="日付" />
      <select value={type} onChange={(e) => setType(e.target.value as TransactionType)} aria-label="種別">
        <option value="expense">支出</option>
        <option value="income">収入</option>
      </select>
      <input
        type="number"
        step={1}
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        placeholder="金額(円)"
        required
        aria-label="金額"
      />
      <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="カテゴリ" required aria-label="カテゴリ" />
      <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="メモ" maxLength={200} aria-label="メモ" />
      <button type="submit" disabled={busy}>
        登録
      </button>
    </form>
  );
}
