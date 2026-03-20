import { API_URL, TOKEN_STORAGE_KEY } from "./constants";
import type {
  ApiError,
  AuthTokens,
  GraphMetrics,
  LoanContract,
  LoanEligibility,
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

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
      // H1: Include cookies on every request (httpOnly cookie auth)
      credentials: "include",
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

  // ── Health ───────────────────────────────────────────────────

  health = {
    check: () => this.get<{ status: string }>("/health"),
  };

  // ── Auth ─────────────────────────────────────────────────────

  auth = {
    register: (data: {
      email: string;
      password: string;
      display_name?: string;
    }) => this.post<User>("/auth/register", data),

    login: (email: string, password: string) =>
      this.post<AuthTokens>("/auth/login", { email, password }),

    me: () => this.get<User>("/auth/me"),

    walletNonce: (walletAddress: string) =>
      this.get<{ nonce: string; wallet_address: string }>(
        `/auth/wallet-nonce?wallet_address=${encodeURIComponent(walletAddress)}`
      ),

    walletLogin: (data: {
      wallet_address: string;
      signature: string;
      message: string;
      nonce: string;
    }) => this.post<AuthTokens>("/auth/wallet-login", data),

    logout: () => this.post<void>("/auth/logout"),
  };

  // ── Trust Score ──────────────────────────────────────────────

  trustScore = {
    calculate: (userId?: string) =>
      this.post<TrustScoreResult>("/trust-score/calculate", { user_id: userId }),
    breakdown: () => this.get<TrustScoreResult>("/trust-score/breakdown"),
    modelInfo: () => this.get("/trust-score/model-info"),
  };

  // ── Sybil ───────────────────────────────────────────────────

  sybil = {
    analyze: () => this.post<SybilAnalysis>("/sybil/analyze"),
  };

  // ── Graph ───────────────────────────────────────────────────

  graph = {
    compute: () => this.post<GraphMetrics>("/graph/compute"),
    recomputeAll: () => this.post<GraphMetrics>("/graph/recompute-all"),
  };

  // ── Loans ───────────────────────────────────────────────────

  loans = {
    create: (data: LoanRequest) =>
      this.post<LoanContract>("/loans/create", data),
    list: () => this.get<LoanContract[]>("/loans"),
    get: (id: string) => this.get<LoanContract>(`/loans/${id}`),
    repay: (contractId: string, amount: number) =>
      this.post<Repayment>("/loans/repay", {
        contract_id: contractId,
        amount,
      }),
    eligibility: () => this.get<LoanEligibility>("/loans/eligibility"),
    marketplace: () =>
      this.get<LoanRequest[]>("/loans/marketplace"),
    fund: (data: { loan_request_id: string }) =>
      this.post<LoanContract>("/loans/fund", data),
  };

  // ── Risk ────────────────────────────────────────────────────

  risk = {
    processDefault: (contractId: string) =>
      this.post("/risk/process-default", { contract_id: contractId }),
    myDefaults: () => this.get("/risk/defaults/me"),
    myPenalties: () => this.get("/risk/penalties/me"),
    myActivePenalties: () => this.get("/risk/penalties/me/active"),
    linkIdentity: (data: {
      provider: string;
      identifier: string;
      is_verified?: boolean;
      verification_method?: string;
    }) => this.post("/risk/identity/link", data),
    myIdentity: () => this.get("/risk/identity/me"),
    myIdentityConfidence: () => this.get("/risk/identity/me/confidence"),
    vouch: (data: {
      borrower_id: string;
      contract_id: string;
      stake_amount: number;
      message?: string;
    }) => this.post("/risk/guarantee/vouch", data),
    myGuaranteesGiven: () => this.get("/risk/guarantee/me/given"),
    myGuaranteesReceived: () => this.get("/risk/guarantee/me/received"),
    myBehavior: () => this.get("/risk/behavior/me"),
  };

  // ── Data Sync ───────────────────────────────────────────────

  data = {
    sync: () => this.post("/data/sync-user-data"),
    connectGitHub: (code: string) =>
      this.post("/data/connect/github", { code }),
    myFeatures: () => this.get("/data/features/me"),
  };

  // ── GitHub ──────────────────────────────────────────────────

  github = {
    connect: (redirectUri?: string) =>
      this.get(
        `/github/connect${redirectUri ? `?redirect_uri=${encodeURIComponent(redirectUri)}` : ""}`
      ),
    callback: (code: string, state: string) =>
      this.post(`/github/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`),
    profile: () => this.get("/github/profile"),
    publicProfile: (username: string) =>
      this.get<{
        login: string;
        name: string | null;
        public_repos: number;
        followers: number;
        account_age_days: number;
        total_stars: number;
        original_repos: number;
        top_languages: string[];
        trust_signals: Record<string, boolean>;
      }>(`/github/public-profile/${encodeURIComponent(username)}`),
  };
}

// ── Singleton ─────────────────────────────────────────────────

export const api = new ApiClient(API_URL);
