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

    eligibility: () => this.get<LoanEligibility>("/loans/eligibility"),
  };

  // ── Health ───────────────────────────────────────────────────

  health = {
    check: () => this.get<{ status: string }>("/health"),
  };

  // ── Intelligence (Demo) ─────────────────────────────────────

  intelligence = {
    simulateScore: (data: {
      income: number;
      income_stability: number;
      wallet_age: number;
      platform_score: number;
      repayment_history: number;
      baseline_score?: number;
    }) => this.post<SimulationResponse>("/simulate-score", data),

    loanRecommend: (data: {
      score: number;
      income: number;
      stability: number;
    }) => this.post<LoanRecommendation>("/loan/recommend", data),

    getUserGraph: (userId: string) =>
      this.get<GraphVisualization>(`/graph/user/${userId}`),

    getSuspiciousClusters: () =>
      this.get<SuspiciousCluster[]>("/graph/suspicious-clusters"),

    getDashboard: (params?: {
      score?: number;
      income?: number;
      stability?: number;
      wallet_age?: number;
      platforms?: number;
    }) => {
      const qs = new URLSearchParams();
      if (params?.score) qs.set("score", String(params.score));
      if (params?.income) qs.set("income", String(params.income));
      if (params?.stability) qs.set("stability", String(params.stability));
      if (params?.wallet_age) qs.set("wallet_age", String(params.wallet_age));
      if (params?.platforms) qs.set("platforms", String(params.platforms));
      const query = qs.toString();
      return this.get<DashboardData>(`/dashboard${query ? `?${query}` : ""}`);
    },
  };
}

export const api = new ApiClient(API_URL);

// Intelligence types
export interface SimulationResponse {
  score: number;
  risk_tier: string;
  delta: number;
  feature_impacts: FeatureImpact[];
  loan_limit: number;
  raw_weighted: number;
}

export interface FeatureImpact {
  feature: string;
  value: number;
  weight: number;
  contribution: number;
  direction: string;
}

export interface LoanRecommendation {
  recommended_amount: number;
  recommended_interest: number;
  risk_level: string;
  reasoning: string;
  collateral_ratio: number;
  max_term_days: number;
  monthly_payment: number;
  confidence: string;
}

export interface GraphNode {
  id: string;
  label: string;
  score: number;
  risk: string;
  is_suspicious: boolean;
  cluster_id: number | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
  edge_type: string;
}

export interface SuspiciousCluster {
  cluster_id: number;
  node_ids: string[];
  reason: string;
  severity: string;
}

export interface GraphVisualization {
  nodes: GraphNode[];
  edges: GraphEdge[];
  clusters: SuspiciousCluster[];
  total_nodes: number;
  total_edges: number;
}

export interface RiskAlert {
  severity: string;
  title: string;
  message: string;
  category: string;
  action: string | null;
}

export interface DashboardData {
  score: number;
  risk_tier: string;
  loan_limit: number;
  alerts: RiskAlert[];
  suggestions: { text: string; impact: string; category: string }[];
  positive_factors: string[];
  negative_factors: string[];
  feature_breakdown: FeatureImpact[];
}
