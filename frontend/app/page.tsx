"use client";

import { GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signOut, type User } from "firebase/auth";
import { useEffect, useState } from "react";

import { getFirebaseAuth } from "@/lib/firebase";

import Transactions from "./Transactions";

export default function Home() {
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => onAuthStateChanged(getFirebaseAuth(), setUser), []);

  async function signIn() {
    setError(null);
    try {
      await signInWithPopup(getFirebaseAuth(), new GoogleAuthProvider());
    } catch {
      setError("ログインに失敗しました");
    }
  }

  if (user === undefined) return <p>読み込み中…</p>;

  return (
    <main>
      <header>
        <h1>Plutus Lite</h1>
        {user ? (
          <div>
            <span>{user.email}</span> <button onClick={() => signOut(getFirebaseAuth())}>ログアウト</button>
          </div>
        ) : (
          <button onClick={signIn}>Google でログイン</button>
        )}
      </header>
      {error && <p className="error">{error}</p>}
      {user && <Transactions user={user} />}
    </main>
  );
}
