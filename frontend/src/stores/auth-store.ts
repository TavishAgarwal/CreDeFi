import { create } from "zustand";
import { api } from "@/lib/api-client";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  /** Email/password login — backend sets httpOnly cookie. */
  login: (email: string, password: string) => Promise<void>;

  /** Register a new account. Does NOT auto-login. */
  register: (email: string, password: string, displayName?: string) => Promise<void>;

  /** Wallet-based login — backend verifies the signed message and sets cookie. */
  walletLogin: (walletAddress: string, signature: string, message: string, nonce: string) => Promise<void>;

  /** Load the current user from the httpOnly cookie (called on app boot). */
  hydrate: () => Promise<void>;

  /** Clear auth state and call backend logout to clear cookie. */
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
      // H1: Backend sets the httpOnly cookie — no token to store client-side
      await api.auth.login(email, password);
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

  walletLogin: async (walletAddress, signature, message, nonce) => {
    set({ isLoading: true, error: null });
    try {
      // H1: Backend sets the httpOnly cookie — no token to store client-side
      await api.auth.walletLogin({
        wallet_address: walletAddress,
        signature,
        message,
        nonce,
      });
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
    // H1: No localStorage check needed — cookie is sent automatically
    set({ isLoading: true });
    try {
      const user = await api.auth.me();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      // Cookie expired or invalid — that's fine, user is just not logged in
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  logout: () => {
    // H1: Call backend to clear the httpOnly cookie
    api.auth.logout().catch(() => {
      /* best-effort — clear local state regardless */
    });
    set({ user: null, isAuthenticated: false, error: null });
  },

  clearError: () => set({ error: null }),
}));
