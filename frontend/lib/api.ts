import type { User } from "firebase/auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

/** API を呼ぶ。ログイン中のユーザーの ID トークンを必ず付ける。user_id は送らない(サーバーがトークンから決める) */
export async function apiFetch<T>(user: User, path: string, init: RequestInit = {}): Promise<T> {
  const token = await user.getIdToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      ...init.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  if (!res.ok) {
    throw new ApiError(res.status, messageFor(res.status));
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

export function messageFor(status: number): string {
  switch (status) {
    case 400:
      return "入力内容に誤りがあります";
    case 401:
      return "ログインし直してください";
    case 403:
      return "このアカウントは利用を許可されていません";
    case 404:
      return "対象の取引が見つかりません";
    default:
      return "エラーが発生しました";
  }
}
