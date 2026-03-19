import { BrowserProvider, JsonRpcSigner } from "ethers";
import { CHAIN_ID } from "./constants";

declare global {
  interface Window {
    ethereum?: {
      isMetaMask?: boolean;
      request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
      on: (event: string, handler: (...args: unknown[]) => void) => void;
      removeListener: (event: string, handler: (...args: unknown[]) => void) => void;
    };
  }
}

export function isMetaMaskInstalled(): boolean {
  return typeof window !== "undefined" && !!window.ethereum?.isMetaMask;
}

export async function getProvider(): Promise<BrowserProvider> {
  if (!isMetaMaskInstalled()) {
    throw new Error("MetaMask is not installed");
  }
  return new BrowserProvider(window.ethereum!);
}

export async function connectWallet(): Promise<{
  address: string;
  signer: JsonRpcSigner;
  provider: BrowserProvider;
}> {
  const provider = await getProvider();

  await window.ethereum!.request({ method: "eth_requestAccounts" });

  const signer = await provider.getSigner();
  const address = await signer.getAddress();

  return { address, signer, provider };
}

export async function ensureCorrectChain(): Promise<void> {
  if (!window.ethereum) return;

  const chainIdHex = `0x${CHAIN_ID.toString(16)}`;
  try {
    await window.ethereum.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: chainIdHex }],
    });
  } catch (err: unknown) {
    const switchError = err as { code?: number };
    if (switchError.code === 4902) {
      throw new Error(
        `Chain ${CHAIN_ID} not configured in MetaMask. Please add it manually.`
      );
    }
    throw err;
  }
}

export async function signMessage(
  signer: JsonRpcSigner,
  message: string
): Promise<string> {
  return signer.signMessage(message);
}

export function buildSignInMessage(address: string, nonce: string): string {
  return [
    "Welcome to CreDeFi!",
    "",
    "Sign this message to verify your wallet ownership.",
    "",
    `Wallet: ${address}`,
    `Nonce: ${nonce}`,
    `Issued At: ${new Date().toISOString()}`,
  ].join("\n");
}

export function onAccountsChanged(
  handler: (accounts: string[]) => void
): () => void {
  if (!window.ethereum) return () => {};
  const wrapped = (...args: unknown[]) => handler(args[0] as string[]);
  window.ethereum.on("accountsChanged", wrapped);
  return () => window.ethereum!.removeListener("accountsChanged", wrapped);
}

export function onChainChanged(handler: (chainId: string) => void): () => void {
  if (!window.ethereum) return () => {};
  const wrapped = (...args: unknown[]) => handler(args[0] as string);
  window.ethereum.on("chainChanged", wrapped);
  return () => window.ethereum!.removeListener("chainChanged", wrapped);
}
