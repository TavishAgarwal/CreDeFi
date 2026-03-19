# CreDeFi — System Architecture & Schema

## System Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend (Next.js)"]
        UI[Landing / Dashboard / Loans]
        WC[Wallet Connect<br/>MetaMask + Ethers.js]
        ZS[Zustand Stores<br/>Auth + Wallet State]
        API_C[Typed API Client]
    end

    subgraph Backend["Backend (FastAPI)"]
        AUTH[JWT Auth<br/>Email + Wallet Signature]
        TSE[AI Trust Score Engine<br/>10-Factor Weighted Scoring]
        SDE[Sybil Detection Engine<br/>5 Detectors + NetworkX]
        TGE[Trust Graph Engine<br/>PageRank + Centrality]
        LS[Loan Service<br/>Full Lifecycle]
    end

    subgraph Blockchain["Smart Contracts (Solidity)"]
        LC[LoanContract.sol<br/>Create → Fund → Repay → Liquidate]
        IRM[InterestRateModel.sol<br/>Utilization Curve + Trust Discount]
        CV[CollateralVault.sol<br/>Deposit / Lock / Liquidate]
        SBT[SoulboundReputationNFT.sol<br/>Non-Transferable Trust Score]
    end

    subgraph Data["PostgreSQL"]
        DB[(Database<br/>13+ Models)]
    end

    UI --> API_C
    WC --> ZS
    API_C -->|REST| AUTH
    API_C -->|REST| TSE
    API_C -->|REST| LS
    AUTH --> DB
    TSE --> DB
    SDE --> DB
    TGE --> DB
    LS --> DB
    LS -->|Mock/Web3| LC
    WC -->|On-Chain| LC
    LC --> IRM
    LC --> CV
    LC --> SBT
```

## Database Schema

```mermaid
erDiagram
    User ||--o{ ConnectedAccount : has
    User ||--o{ IncomeSource : has
    User ||--o{ TrustScore : has
    User ||--o{ LoanRequest : borrows
    User ||--o{ LoanContract : lends
    User ||--o{ SybilAnalysis : analyzed
    User ||--o{ GraphFeatureVector : has
    User ||--o{ SessionFingerprint : has

    LoanRequest ||--o| LoanContract : funded_by
    LoanContract ||--o{ Repayment : has
    LoanContract ||--o{ Transaction : has

    SybilAnalysis ||--o{ WalletCluster : contains

    User {
        uuid id PK
        string email
        string wallet_address
        string display_name
        string hashed_password
        boolean is_active
        timestamp created_at
    }

    TrustScore {
        uuid id PK
        uuid user_id FK
        float score "300-1000"
        string risk_tier "EXCELLENT|GOOD|FAIR|POOR|VERY_POOR"
        json feature_contributions
        json penalties
        float loan_limit
        timestamp computed_at
    }

    ConnectedAccount {
        uuid id PK
        uuid user_id FK
        enum provider "GITHUB|UPWORK|STRIPE|LINKEDIN"
        string account_id
        json metadata
        timestamp last_synced
    }

    IncomeSource {
        uuid id PK
        uuid user_id FK
        float amount
        string currency
        enum frequency "WEEKLY|BIWEEKLY|MONTHLY"
        boolean is_verified
    }

    LoanRequest {
        uuid id PK
        uuid borrower_id FK
        float amount
        string currency
        int duration_days
        int interest_rate_bps
        int collateral_ratio_bps
        enum risk_tier
        enum status "PENDING|ACTIVE|FUNDED|REPAID|DEFAULTED|CANCELLED"
    }

    LoanContract {
        uuid id PK
        uuid loan_request_id FK
        uuid lender_id FK
        float principal
        float total_repaid
        string chain_tx_hash
        timestamp funded_at
        timestamp due_at
    }

    Repayment {
        uuid id PK
        uuid loan_contract_id FK
        float amount
        string tx_hash
        enum status "PENDING|CONFIRMED|FAILED"
    }

    Transaction {
        uuid id PK
        uuid from_user_id FK
        uuid to_user_id FK
        float amount
        string currency
        enum type "DISBURSEMENT|REPAYMENT|COLLATERAL_LOCK|COLLATERAL_RELEASE"
        enum status "PENDING|CONFIRMED|FAILED"
    }

    SybilAnalysis {
        uuid id PK
        uuid user_id FK
        float sybil_score "0.0-1.0"
        enum verdict "CLEAN|SUSPICIOUS|LIKELY_SYBIL"
        json detector_results
    }

    WalletCluster {
        uuid id PK
        uuid analysis_id FK
        string label
        json addresses
        float similarity_score
    }

    SessionFingerprint {
        uuid id PK
        uuid user_id FK
        string ip_hash
        string device_hash
        int session_count
    }

    TrustGraphEdge {
        uuid id PK
        uuid source_user_id FK
        uuid target_user_id FK
        string edge_type
        float weight
    }

    GraphFeatureVector {
        uuid id PK
        uuid user_id FK
        float pagerank
        float betweenness
        float closeness
        float clustering
        float reciprocity
        float edge_diversity
        float reputation_score
    }

    ExchangeRate {
        uuid id PK
        string base_currency
        string quote_currency
        float rate
        timestamp fetched_at
    }

    CurrencyConfig {
        uuid id PK
        string code
        float risk_score
        boolean is_active
    }
```

## AI Trust Score Engine — Scoring Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    RAW DATA SOURCES                         │
│  Connected Accounts · Income · Wallet · Loan History        │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               FEATURE EXTRACTION (10 Factors)               │
│                                                             │
│  Loan Reliability .... 16%    Platform Quality .... 10%     │
│  Income .............. 13%    Wallet Age .......... 8%      │
│  Income Stability .... 12%    Tx Diversity ........ 6%      │
│  Graph Reputation .... 12%    Growth Trend ........ 6%      │
│  Currency Risk ....... 12%    Account Behavior .... 5%      │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  ANTI-FRAUD PENALTIES                        │
│                                                             │
│  • Circular transaction detection                           │
│  • Sybil verdict penalty (0.5x multiplier)                  │
│  • Velocity change penalty                                  │
│  • Score decay over time                                    │
│  • Gaming pattern detection                                 │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SIGMOID MAPPING → 300–1000 SCORE               │
│                                                             │
│  300 ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 1000  │
│      VERY_POOR  POOR   FAIR    GOOD    EXCELLENT            │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT                                    │
│  Score: 782 │ Tier: EXCELLENT │ Loan Limit: $50,000         │
└─────────────────────────────────────────────────────────────┘
```

## Smart Contract Interaction Flow

```
Borrower                    LoanContract              CollateralVault
   │                             │                          │
   │  1. createLoan()            │                          │
   │────────────────────────────▶│   lock collateral        │
   │                             │─────────────────────────▶│
   │                             │                          │
   │         Lender              │                          │
   │           │  2. fundLoan()  │                          │
   │           │────────────────▶│                          │
   │  ◀────── │ principal sent   │                          │
   │                             │                          │
   │  3. repay()                 │                          │
   │────────────────────────────▶│                          │
   │           │  ◀──────────────│ repayment to lender      │
   │                             │                          │
   │  (if fully repaid)          │   unlock collateral      │
   │  ◀─────────────────────────│─────────────────────────▶│
   │                             │                          │
   │  (if defaulted)  Liquidator │                          │
   │                    │  4. liquidate()                    │
   │                    │───────▶│   seize + bonus          │
   │                    │  ◀─────│──────────────────────────▶│
```
