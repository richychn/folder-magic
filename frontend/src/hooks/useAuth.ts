import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../api/client";

type UserProfile = {
  email: string;
  name?: string;
  picture?: string;
};

type AuthResponse = {
  authenticated: boolean;
  user?: UserProfile;
};

export const useAuth = () => {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<UserProfile | undefined>(undefined);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<AuthResponse>("/api/auth/me");
      setAuthenticated(Boolean(data.authenticated));
      setUser(data.user);
    } catch (error) {
      console.error("Failed to fetch auth state", error);
      setAuthenticated(false);
      setUser(undefined);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { loading, authenticated, user, refresh };
};
