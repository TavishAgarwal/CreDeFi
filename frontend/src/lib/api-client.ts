import { API_URL, TOKEN_STORAGE_KEY } from "./constants";
import type {
  ApiError,
  AuthTokens,
  GraphMetrics,
  LoanContract,
  LoanRequest,
  Repayment,
  SybilAnalysis,
  TrustScoreResult,
  User,
} from "@/types";

// ── Core fetch wrapper ───────────────────────────────────────────

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let detail = `Request failed with status ${res.status}`;
      try {
        const body = await res.json();
        detail = body.detail ?? detail;
      } catch {
        /* non-JSON error body */
      }
      const err: ApiError = { detail, status: res.status };
      throw err;
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  }

  private get<T>(path: string) {
    return this.request<T>(path, { method: "GET" });
  }

  private post<T>(path: string, body?: unknown) {
    return this.request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  // ── Auth ─────────────────────────────────────────────────────

  auth = {
    register: (data: {
      email: string;
      password: string;
      display_name?: string;
    }) => this.post<User>("/auth/register", data),

    login: (email: string, password: string) => {
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);
      return this.request<AuthTokens>("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });
    },

    me: () => this.get<User>("/auth/me"),

    walletLogin: (data: { wallet_address: string; signature: string; message: string }) =>
      this.post<AuthTokens>("/auth/wallet-login", data),
  };

  // ── Trust Score ──────────────────────────────────────────────

  trustScore = {
    calculate: () =>
      this.post<TrustScoreResult>("/trust-score/calculate"),
  };

  // ── Sybil ────────────────────────────────────────────────────

  sybil = {
    analyze: () => this.post<SybilAnalysis>("/sybil/analyze"),
  };

  // ── Graph ────────────────────────────────────────────────────

  graph = {
    compute: () => this.post<GraphMetrics>("/graph/compute"),
  };

  // ── Loans ────────────────────────────────────────────────────

  loans = {
    create: (data: {
      amount: number;
      currency: string;
      duration_days: number;
    }) => this.post<LoanRequest>("/loans/request", data),

    marketplace: (params?: {
      currency?: string;
      min_amount?: number;
      max_amount?: number;
    }) => {
      const qs = new URLSearchParams();
      if (params?.currency) qs.set("currency", params.currency);
      if (params?.min_amount) qs.set("min_amount", String(params.min_amount));
      if (params?.max_amount) qs.set("max_amount", String(params.max_amount));
      const query = qs.toString();
      return this.get<LoanRequest[]>(
        `/loans/marketplace${query ? `?${query}` : ""}`
      );
    },

    fund: (data: { loan_request_id: string }) =>
      this.post<LoanContract>("/loans/fund", data),

    repay: (data: { loan_contract_id: string; amount: number }) =>
      this.post<Repayment>("/loans/repay", data),

    history: () => this.get<LoanRequest[]>("/loans/history"),
  };

  // ── Health ───────────────────────────────────────────────────

  health = {
    check: () => this.get<{ status: string }>("/health"),
  };
}

export const api = new ApiClient(API_URL);
