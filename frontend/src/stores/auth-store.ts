import { create } from "zustand";
import { api } from "@/lib/api-client";
import { TOKEN_STORAGE_KEY } from "@/lib/constants";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  /** Email/password login — stores JWT and fetches user profile. */
  login: (email: string, password: string) => Promise<void>;

  /** Register a new account. Does NOT auto-login. */
  register: (email: string, password: string, displayName?: string) => Promise<void>;

  /** Wallet-based login — backend verifies the signed message. */
  walletLogin: (walletAddress: string, signature: string, message: string) => Promise<void>;

  /** Load the current user from a stored JWT (called on app boot). */
  hydrate: () => Promise<void>;

  /** Clear auth state and remove stored token. */
  logout: () => void;

  /** Reset transient error state. */
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const tokens = await api.auth.login(email, password);
      localStorage.setItem(TOKEN_STORAGE_KEY, tokens.access_token);
      const user = await api.auth.me();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const message = (err as { detail?: string }).detail ?? "Login failed";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  register: async (email, password, displayName) => {
    set({ isLoading: true, error: null });
    try {
      await api.auth.register({ email, password, display_name: displayName });
      set({ isLoading: false });
    } catch (err: unknown) {
      const message = (err as { detail?: string }).detail ?? "Registration failed";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  walletLogin: async (walletAddress, signature, message) => {
    set({ isLoading: true, error: null });
    try {
      const tokens = await api.auth.walletLogin({
        wallet_address: walletAddress,
        signature,
        message,
      });
      localStorage.setItem(TOKEN_STORAGE_KEY, tokens.access_token);
      const user = await api.auth.me();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const message_ =
        (err as { detail?: string }).detail ?? "Wallet login failed";
      set({ error: message_, isLoading: false });
      throw err;
    }
  },

  hydrate: async () => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) return;

    set({ isLoading: true });
    try {
      const user = await api.auth.me();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    set({ user: null, isAuthenticated: false, error: null });
  },

  clearError: () => set({ error: null }),
}));
