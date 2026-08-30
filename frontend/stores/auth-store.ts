/**
 * Auth state management with Zustand.
 */
import { create } from "zustand";
import { api } from "@/lib/api/client";
import { trackEvent } from "@/lib/analytics";
import type { User, AuthResponse, LoginRequest, RegisterRequest } from "@/lib/api/types";
interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  // Actions
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  initialize: () => Promise<void>;
}
export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  login: async (data: LoginRequest) => {
    const response = await api.post<AuthResponse>("/auth/login", data);
    api.setTokens(response.access_token, response.refresh_token);
    await get().fetchUser();
  },
  register: async (data: RegisterRequest) => {
    const response = await api.post<AuthResponse>("/auth/register", data);
    api.setTokens(response.access_token, response.refresh_token);
    await get().fetchUser();
  },
  logout: () => {
    api.clearTokens();
    set({ user: null, isAuthenticated: false });
  },
  fetchUser: async () => {
    try {
      const user = await api.get<User>("/auth/me");
      set({ user, isAuthenticated: true });
    } catch (err) {
      console.error("fetchUser failed:", err);
      set({ user: null, isAuthenticated: false });
      api.clearTokens();
    }
  },
  initialize: async () => {
    set({ isLoading: true });
    if (api.isAuthenticated()) {
      await get().fetchUser();
      if (get().isAuthenticated) {
        trackEvent("session_started");
      }
    }
    set({ isLoading: false });
  },
}));
