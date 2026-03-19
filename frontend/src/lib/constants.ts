export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export const CHAIN_ID = Number(process.env.NEXT_PUBLIC_CHAIN_ID ?? "31337");

export const CONTRACT_ADDRESSES = {
  loan: process.env.NEXT_PUBLIC_LOAN_CONTRACT_ADDRESS ?? "",
  vault: process.env.NEXT_PUBLIC_VAULT_CONTRACT_ADDRESS ?? "",
  nft: process.env.NEXT_PUBLIC_NFT_CONTRACT_ADDRESS ?? "",
  rateModel: process.env.NEXT_PUBLIC_RATE_MODEL_ADDRESS ?? "",
} as const;

export const TOKEN_STORAGE_KEY = "credefi_auth_token";

export const RISK_TIER_LABELS: Record<string, string> = {
  EXCELLENT: "Excellent",
  GOOD: "Good",
  FAIR: "Fair",
  POOR: "Poor",
  VERY_POOR: "Very Poor",
};

export const RISK_TIER_COLORS: Record<string, string> = {
  EXCELLENT: "text-emerald-400",
  GOOD: "text-green-400",
  FAIR: "text-yellow-400",
  POOR: "text-orange-400",
  VERY_POOR: "text-red-400",
};
