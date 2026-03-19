// ── Auth ─────────────────────────────────────────────────────────

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  display_name: string | null;
  wallet_address: string | null;
  is_active: boolean;
  created_at: string;
}

// ── Wallet ───────────────────────────────────────────────────────

export type ConnectionStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";

// ── Trust Score ──────────────────────────────────────────────────

export type RiskTier =
  | "EXCELLENT"
  | "GOOD"
  | "FAIR"
  | "POOR"
  | "VERY_POOR";

export interface TrustScoreResult {
  score: number;
  risk_tier: RiskTier;
  loan_limit: number;
  penalties: PenaltyDetail[];
  feature_contributions: Record<string, number>;
  computed_at: string;
}

export interface PenaltyDetail {
  name: string;
  deduction: number;
  reason: string;
}

// ── Loans ────────────────────────────────────────────────────────

export type LoanStatus =
  | "PENDING"
  | "ACTIVE"
  | "FUNDED"
  | "REPAID"
  | "DEFAULTED"
  | "LIQUIDATED"
  | "CANCELLED";

export interface LoanRequest {
  id: string;
  borrower_id: string;
  amount: number;
  currency: string;
  duration_days: number;
  interest_rate_bps: number;
  collateral_ratio_bps: number;
  risk_tier: RiskTier;
  status: LoanStatus;
  created_at: string;
}

export interface LoanContract {
  id: string;
  loan_request_id: string;
  lender_id: string;
  funded_at: string;
  due_at: string;
  principal: number;
  total_repaid: number;
  status: LoanStatus;
}

export interface Repayment {
  id: string;
  loan_contract_id: string;
  amount: number;
  tx_hash: string | null;
  created_at: string;
}

// ── Sybil ────────────────────────────────────────────────────────

export type SybilVerdict = "CLEAN" | "SUSPICIOUS" | "LIKELY_SYBIL";

export interface SybilAnalysis {
  sybil_score: number;
  verdict: SybilVerdict;
  detectors: DetectorDetail[];
  analyzed_at: string;
}

export interface DetectorDetail {
  name: string;
  score: number;
  weight: number;
  flags: string[];
}

// ── Graph ────────────────────────────────────────────────────────

export interface GraphMetrics {
  user_id: string;
  reputation_score: number;
  pagerank: number;
  betweenness: number;
  closeness: number;
  clustering: number;
  reciprocity: number;
  edge_diversity: number;
  computed_at: string;
}

// ── Transaction ──────────────────────────────────────────────────

export interface Transaction {
  id: string;
  from_user_id: string;
  to_user_id: string;
  amount: number;
  currency: string;
  tx_hash: string | null;
  status: string;
  created_at: string;
}

// ── API ──────────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}
