import { create } from "zustand";
import { BrowserProvider, JsonRpcSigner } from "ethers";
import {
  connectWallet,
  ensureCorrectChain,
  isMetaMaskInstalled,
  signMessage,
  buildSignInMessage,
} from "@/lib/wallet";
import { api } from "@/lib/api-client";
import type { ConnectionStatus } from "@/types";

interface WalletState {
  address: string | null;
  status: ConnectionStatus;
  provider: BrowserProvider | null;
  signer: JsonRpcSigner | null;
  chainId: number | null;
  error: string | null;
  demoMode: boolean;

  /** Prompt MetaMask connection and store provider/signer. */
  connect: () => Promise<void>;

  /** Drop wallet state (does NOT disconnect MetaMask itself). */
  disconnect: () => void;

  /** Enter demo mode with sample data. */
  enableDemo: () => void;

  /** Exit demo mode. */
  disableDemo: () => void;

  /** Sign the standard CreDeFi login message. Returns { signature, message }. */
  signLoginMessage: () => Promise<{ signature: string; message: string; nonce: string }>;

  /** Update address from MetaMask accountsChanged event. */
  handleAccountsChanged: (accounts: string[]) => void;

  /** Update chainId from MetaMask chainChanged event. */
  handleChainChanged: (chainIdHex: string) => void;

  clearError: () => void;
}

const DEMO_ADDRESS = "0xDe0000000000000000000000000000000000dEm0";

export const useWalletStore = create<WalletState>((set, get) => ({
  address: null,
  status: "disconnected",
  provider: null,
  signer: null,
  chainId: null,
  error: null,
  demoMode: false,

  connect: async () => {
    if (!isMetaMaskInstalled()) {
      set({ error: "MetaMask is not installed", status: "error" });
      return;
    }

    set({ status: "connecting", error: null });
    try {
      await ensureCorrectChain();
      const { address, signer, provider } = await connectWallet();
      const network = await provider.getNetwork();

      set({
        address,
        signer,
        provider,
        chainId: Number(network.chainId),
        status: "connected",
        demoMode: false,
      });
    } catch (err: unknown) {
      const msg =
        (err as { message?: string }).message ?? "Wallet connection failed";
      set({ status: "error", error: msg });
    }
  },

  disconnect: () => {
    set({
      address: null,
      signer: null,
      provider: null,
      chainId: null,
      status: "disconnected",
      error: null,
      demoMode: false,
    });
  },

  enableDemo: () => {
    set({
      demoMode: true,
      address: DEMO_ADDRESS,
      status: "connected",
      error: null,
    });
  },

  disableDemo: () => {
    set({
      demoMode: false,
      address: null,
      status: "disconnected",
      provider: null,
      signer: null,
      chainId: null,
      error: null,
    });
  },

  signLoginMessage: async () => {
    const { signer, address } = get();
    if (!signer || !address) {
      throw new Error("Wallet not connected");
    }

    // C5: Request a server-side nonce (single-use, 5-min TTL)
    const { nonce } = await api.auth.walletNonce(address);
    const message = buildSignInMessage(address, nonce);
    const signature = await signMessage(signer, message);

    return { signature, message, nonce };
  },

  handleAccountsChanged: (accounts) => {
    if (accounts.length === 0) {
      get().disconnect();
    } else {
      set({ address: accounts[0] });
    }
  },

  handleChainChanged: (chainIdHex) => {
    set({ chainId: parseInt(chainIdHex, 16) });
  },

  clearError: () => set({ error: null }),
}));
