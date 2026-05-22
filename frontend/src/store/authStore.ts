import { create } from "zustand";
import { User } from "../types";

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  setUser: (user: User, token: string) => void;
  clearAuth: () => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
}

// Rehydrate from localStorage on load
const storedToken = localStorage.getItem("leaseiq_token");
const storedUser = localStorage.getItem("leaseiq_user");

export const useAuthStore = create<AuthState>((set) => ({
  user: storedUser ? JSON.parse(storedUser) : null,
  token: storedToken || null,
  isLoading: false,
  error: null,
  setUser: (user: User, token: string) => {
    localStorage.setItem("leaseiq_token", token);
    localStorage.setItem("leaseiq_user", JSON.stringify(user));
    set({
      user,
      token,
      error: null,
      isLoading: false,
    });
  },
  clearAuth: () => {
    localStorage.removeItem("leaseiq_token");
    localStorage.removeItem("leaseiq_user");
    set({
      user: null,
      token: null,
      error: null,
    });
  },
  setError: (error: string | null) =>
    set({
      error,
      isLoading: false,
    }),
  setLoading: (isLoading: boolean) =>
    set({
      isLoading,
    }),
}));
