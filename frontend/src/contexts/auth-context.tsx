import { createContext, useEffect, useState, type ReactNode } from 'react';
import { login as apiLogin, register as apiRegister } from '../api/auth-api';
import type { User } from '../types';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (full_name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

function decodeUser(token: string): User | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return { id: payload.sub, email: payload.email, full_name: payload.full_name };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [user, setUser] = useState<User | null>(() => {
    const t = localStorage.getItem('token');
    return t ? decodeUser(t) : null;
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (token) {
      setUser(decodeUser(token));
    }
  }, [token]);

  async function login(email: string, password: string) {
    setIsLoading(true);
    try {
      const res = await apiLogin(email, password);
      localStorage.setItem('token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    } finally {
      setIsLoading(false);
    }
  }

  async function register(full_name: string, email: string, password: string) {
    setIsLoading(true);
    try {
      await apiRegister(full_name, email, password);
    } finally {
      setIsLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
