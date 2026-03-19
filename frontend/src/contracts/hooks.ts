/**
 * React hooks for interacting with CreDeFi smart contracts via ethers.js.
 * Uses the wallet signer from the wallet store.
 */

"use client";

import { useMemo } from "react";
import { Contract, type ContractRunner } from "ethers";
import { useWalletStore } from "@/stores/wallet-store";
import { CONTRACT_ADDRESSES } from "@/lib/constants";

// ─── ABI imports ─────────────────────────────────────────────────
// These are populated by contracts/scripts/export-abis.js
import LoanContractABI from "./abis/LoanContract.json";
import CollateralVaultABI from "./abis/CollateralVault.json";
import SoulboundReputationNFTABI from "./abis/SoulboundReputationNFT.json";
import InterestRateModelABI from "./abis/InterestRateModel.json";
import MockERC20ABI from "./abis/MockERC20.json";

// ─── Types ───────────────────────────────────────────────────────

export interface ContractInstances {
  loan: Contract | null;
  vault: Contract | null;
  nft: Contract | null;
  rateModel: Contract | null;
}

// ─── Hook ────────────────────────────────────────────────────────

export function useContracts(): ContractInstances {
  const { signer, provider } = useWalletStore();

  return useMemo(() => {
    const runner: ContractRunner | null = signer ?? provider ?? null;
    if (!runner) {
      return { loan: null, vault: null, nft: null, rateModel: null };
    }

    const make = (addr: string, abi: { abi: unknown[] }) =>
      addr ? new Contract(addr, abi.abi, runner) : null;

    return {
      loan: make(CONTRACT_ADDRESSES.loan, LoanContractABI),
      vault: make(CONTRACT_ADDRESSES.vault, CollateralVaultABI),
      nft: make(CONTRACT_ADDRESSES.nft, SoulboundReputationNFTABI),
      rateModel: make(CONTRACT_ADDRESSES.rateModel, InterestRateModelABI),
    };
  }, [signer, provider]);
}

/**
 * Get a typed ERC-20 Contract instance for approvals and balance checks.
 */
export function useERC20(tokenAddress: string): Contract | null {
  const { signer, provider } = useWalletStore();
  return useMemo(() => {
    const runner = signer ?? provider ?? null;
    if (!runner || !tokenAddress) return null;
    return new Contract(tokenAddress, MockERC20ABI.abi, runner);
  }, [signer, provider, tokenAddress]);
}
