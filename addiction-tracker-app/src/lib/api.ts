import type { AssessmentResult, DailyLog, Substance, User } from "@/types";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8011";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `API error ${response.status}`);
  }

  return response.json();
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),
  listUsers: () => request<User[]>("/api/users"),
  createUser: (body: Omit<User, "id"> & { password_hash?: string | null }) =>
    request<User>("/api/users", { method: "POST", body: JSON.stringify(body) }),
  listSubstances: () => request<Substance[]>("/api/substances"),
  createSubstance: (body: Omit<Substance, "id">) =>
    request<Substance>("/api/substances", { method: "POST", body: JSON.stringify(body) }),
  listDailyLogs: () => request<DailyLog[]>("/api/daily-logs"),
  createDailyLog: (body: Omit<DailyLog, "id">) =>
    request<DailyLog>("/api/daily-logs", { method: "POST", body: JSON.stringify(body) }),
  assess: (body: {
    craving_level: number;
    substance_name: string;
    city?: string;
    postal_code?: string;
    cbt_notes?: string;
  }) => request<AssessmentResult>("/api/assessment", { method: "POST", body: JSON.stringify(body) }),
};
