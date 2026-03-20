# CreDeFi — Decentralized Credit Intelligence Platform

> AI-powered credit scoring for DeFi. Turn your Web2 work history, on-chain activity, and verified identity into real borrowing power — no bank account required.

## Architecture

```
┌──────────────────┐     ┌──────────────────────┐     ┌───────────────────┐
│   Next.js 16     │────▶│   FastAPI Backend     │────▶│  Solidity Smart   │
│   Frontend       │     │                      │     │  Contracts        │
│                  │     │  • AI Trust Score    │     │                   │
│  • Tailwind CSS  │     │    Engine (10-factor) │     │  • LoanContract   │
│  • Ethers.js     │     │  • ML Default        │     │  • InterestRate   │
│  • Zustand       │     │    Prediction        │     │  • CollateralVault│
│  • Recharts      │     │  • Sybil Detection   │     │  • SoulboundNFT   │
│  • html2canvas   │     │  • Trust Graph       │     │                   │
│                  │     │  • PostgreSQL + JWT   │     │  • Hardhat        │
└──────────────────┘     └──────────────────────┘     └───────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **AI Trust Score** | 10-factor weighted scoring with anti-fraud penalties, sigmoid mapping (300–1000 range), and ML default prediction |
| **Score Simulator** | Real-time "what-if" analysis with 5 interactive sliders and per-feature impact breakdown |
| **Loan System** | Full lifecycle: request → fund → repay → liquidate, with AI-powered recommendations |
| **Trust Graph** | Network visualization with node relationships, suspicious cluster detection, and Sybil analysis |
| **Credit Passport** | Exportable card showing score, risk tier, loan limit, and connected platforms (PNG download) |
| **Risk Alerts** | Context-aware alerts based on income stability, wallet age, platform count, and repayment behavior |
| **Smart Contracts** | 4 Solidity contracts: loan lifecycle, interest rate model, collateral vault, soulbound reputation NFT |
| **Demo Mode** | Full exploration without wallet — all features work with realistic mock data |
| **Wallet Auth** | MetaMask connection with message signing and JWT token exchange |

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | Next.js 16, Tailwind CSS, Ethers.js, Zustand, Recharts, html2canvas |
| Backend | FastAPI, SQLAlchemy (async), PostgreSQL, Alembic, JWT, NumPy |
| AI Engine | Custom weighted scoring (10 features), sigmoid mapping, ML default predictor |
| Contracts | Solidity ^0.8.27, Hardhat, OpenZeppelin |
| Testing | Pytest (backend), Hardhat tests (contracts) |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or use Docker)

### 1. Backend

```bash
cd backend
cp .env.example .env          # Edit with your DB credentials
pip install -r requirements.txt
# Run database migrations
alembic upgrade head
# Start the server
uvicorn main:app --reload --port 8000
```

### 2. Smart Contracts

```bash
cd contracts
npm install
npx hardhat compile
# Optional: deploy to local network
npx hardhat node                          # Terminal 1
npx hardhat run scripts/deploy.js --network localhost  # Terminal 2
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local    # Edit API URL and contract addresses
npm install
npm run dev
```

The app will be available at **http://localhost:3000**.

### Environment Variables

See `backend/.env.example` and `frontend/.env.example` for all required variables.

## Demo Mode

CreDeFi includes a full **demo mode** that works without any backend or wallet:

1. Open `http://localhost:3000`
2. Click **"Try Demo"** on the wallet gate screen
3. Explore the full dashboard with sample data:
   - Trust Score gauge with recalculate button
   - Score Simulator with interactive sliders
   - Trust Network Graph with suspicious cluster detection
   - Loan Request form with AI recommendations
   - Credit Passport with PNG export
   - Transaction history and platform connections

Demo mode uses realistic mock data and makes zero API calls.

## Project Structure

```
CreDeFi/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI route handlers (12 files)
│   │   ├── services/      # Business logic (21 service modules)
│   │   ├── models/        # SQLAlchemy models (11 files, 13+ tables)
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── ml/            # ML inference and model loading
│   │   ├── contracts/     # Blockchain client integration
│   │   ├── core/          # Config, security, dependencies
│   │   ├── db/            # Database session management
│   │   └── utils/         # Shared utilities
│   ├── tests/             # Pytest test suite
│   ├── data/              # Seed data and fixtures
│   └── alembic/           # Database migrations
├── frontend/
│   └── src/
│       ├── app/           # Next.js pages (7 routes)
│       ├── components/    # UI components (13 components)
│       ├── stores/        # Zustand state stores
│       ├── hooks/         # Custom React hooks
│       ├── lib/           # API client, wallet, utilities
│       ├── providers/     # Context providers
│       ├── contracts/     # ABI files
│       └── types/         # TypeScript type definitions
├── contracts/
│   ├── contracts/         # 4 Solidity smart contracts
│   ├── scripts/           # Deploy + ABI export scripts
│   └── test/              # Hardhat contract tests
└── docs/                  # Schema documentation, research papers
```

## API Endpoints

### Core
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Email/password login |
| POST | `/auth/wallet-login` | MetaMask wallet auth |

### Intelligence (Demo-Ready)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/simulate-score` | Score simulation from 5 features |
| POST | `/loan/recommend` | AI loan recommendation |
| GET | `/graph/user/{id}` | Trust graph visualization |
| GET | `/graph/suspicious-clusters` | Detected suspicious clusters |
| GET | `/dashboard` | Full dashboard with alerts + suggestions |

### Trust Score
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/trust-score/calculate` | Calculate trust score |
| GET | `/trust-score/breakdown` | Full explainable breakdown |
| GET | `/trust-score/model-info` | ML model metadata |

### Loans
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/loans/request` | Create loan request |
| GET | `/loans/marketplace` | Browse available loans |
| POST | `/loans/fund` | Fund a loan (lender) |
| POST | `/loans/repay` | Repay a loan |
| GET | `/loans/eligibility` | Check borrow eligibility |
| GET | `/loans/history` | Loan history |

### Risk & Graph
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/graph/compute` | Compute trust graph metrics |
| POST | `/risk/process-default` | Process loan default |
| POST | `/risk/guarantee/vouch` | Vouch for a borrower |
| GET | `/risk/behavior/{id}` | Repayment behavior stats |

## License

MIT
