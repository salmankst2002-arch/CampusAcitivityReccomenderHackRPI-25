// front_end/src/auth/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from "react";

type AuthContextValue = {
  userId: number | null;
  setUserId: (id: number | null) => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = "campus_match_user_id";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [userId, setUserIdState] = useState<number | null>(() => {
    // Load from localStorage once on mount
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    const n = Number(stored);
    return Number.isFinite(n) ? n : null;
  });

  const setUserId = (id: number | null) => {
    setUserIdState(id);
    if (id === null) {
      window.localStorage.removeItem(STORAGE_KEY);
    } else {
      window.localStorage.setItem(STORAGE_KEY, String(id));
    }
  };

  return (
    <AuthContext.Provider value={{ userId, setUserId }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return ctx;
}

