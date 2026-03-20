#!/usr/bin/env bash
# seed-env.sh — Auto-populate .env files from deployed_addresses.json
# Usage: ./scripts/seed-env.sh [path-to-deployed_addresses.json]
set -euo pipefail

ADDR_FILE="${1:-contracts/deployed_addresses.json}"

if [ ! -f "$ADDR_FILE" ]; then
  echo "❌ $ADDR_FILE not found — deploy contracts first"
  exit 1
fi

# Parse JSON (portable — no jq required)
get_addr() { python3 -c "import json,sys; print(json.load(open('$ADDR_FILE'))['$1'])" 2>/dev/null; }

LOAN_ADDR=$(get_addr "LoanContract")
VAULT_ADDR=$(get_addr "CollateralVault")
NFT_ADDR=$(get_addr "SoulboundReputationNFT")
RATE_ADDR=$(get_addr "InterestRateModel")
USDC_ADDR=$(get_addr "MockUSDC")
WETH_ADDR=$(get_addr "MockWETH")
RPC_URL=$(get_addr "rpcUrl")

# Hardhat account #0 private key (deterministic for local dev)
HARDHAT_PK="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "placeholder-fernet-key")

# ── Backend .env ──────────────────────────────────────────────────
cat > backend/.env <<EOF
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/credefi
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
TOKEN_ENCRYPTION_KEY=$FERNET_KEY
CORS_ORIGINS=["http://localhost:3000"]
RPC_URL=$RPC_URL
CHAIN_PRIVATE_KEY=$HARDHAT_PK
LOAN_CONTRACT_ADDRESS=$LOAN_ADDR
VAULT_CONTRACT_ADDRESS=$VAULT_ADDR
NFT_CONTRACT_ADDRESS=$NFT_ADDR
RATE_MODEL_ADDRESS=$RATE_ADDR
USDC_ADDRESS=$USDC_ADDR
WETH_ADDRESS=$WETH_ADDR
DEBUG=true
EOF

echo "✅ backend/.env written"

# ── Frontend .env.local ──────────────────────────────────────────
cat > frontend/.env.local <<EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CHAIN_ID=31337
NEXT_PUBLIC_LOAN_CONTRACT_ADDRESS=$LOAN_ADDR
NEXT_PUBLIC_VAULT_CONTRACT_ADDRESS=$VAULT_ADDR
NEXT_PUBLIC_NFT_CONTRACT_ADDRESS=$NFT_ADDR
NEXT_PUBLIC_RATE_MODEL_ADDRESS=$RATE_ADDR
EOF

echo "✅ frontend/.env.local written"
echo "📋 Contract addresses loaded from $ADDR_FILE"
