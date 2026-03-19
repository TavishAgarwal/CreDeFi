# CreDeFi — Decentralized Credit Scoring & Lending

Freelancers and digital nomads are locked out of traditional credit. CreDeFi bridges the gap by turning verified Web2 work history, on-chain activity, and AI-driven analytics into DeFi borrowing power.

## Architecture

```
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Next.js    │───▶│   FastAPI         │───▶│  Solidity        │
│   Frontend   │    │   Backend         │    │  Smart Contracts │
│              │    │                   │    │                  │
│  • Tailwind  │    │  • AI Trust Score │    │  • LoanContract  │
│  • Ethers.js │    │  • PostgreSQL     │    │  • InterestRate  │
│  • Zustand   │    │  • JWT Auth       │    │  • Hardhat       │
└──────────────┘    └──────────────────┘    └──────────────────┘
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 16, Tailwind CSS, Ethers.js, Zustand |
| Backend | FastAPI, SQLAlchemy (async), PostgreSQL, Alembic, JWT |
| Contracts | Solidity ^0.8.27, Hardhat, OpenZeppelin |
| AI Engine | Custom weighted scoring (numpy), no LLM wrappers |

## Key Features

- **AI Trust Score Engine** — 10-factor weighted scoring with anti-fraud penalties and sigmoid mapping (300-1000 range)
- **Smart Contracts** — Full loan lifecycle (create → fund → repay → liquidate) with on-chain interest rate model
- **Wallet Auth** — MetaMask connection with message signing
- **13+ Database Models** — Core, Loans, Sybil, Graph, Currency domains

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt

# Contracts
cd contracts && npm install && npx hardhat compile

# Frontend
cd frontend && npm install && npm run dev
```
