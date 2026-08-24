"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { User } from "@/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setLoading(false);
        return;
      }
      const data = await api.getMe();
      setUser(data);
    } catch {
      localStorage.removeItem("token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email: string, password: string) => {
    const data = await api.login(email, password);
    localStorage.setItem("token", data.access_token);
    const userData = await api.getMe();
    setUser(userData);
    return data;
  };

  const register = async (name: string, email: string, password: string) => {
    const data = await api.register(name, email, password);
    localStorage.setItem("token", data.access_token);
    const userData = await api.getMe();
    setUser(userData);
    return data;
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  const loadDemo = async () => {
    const data = await api.loadDemo();
    localStorage.setItem("token", data.token);
    const userData = await api.getMe();
    setUser(userData);
    return data;
  };

  return { user, loading, login, register, logout, loadDemo, checkAuth };
}
