import { useEffect, useState } from "react";
import Auth from "../Auth";
import AppLayout from "./AppLayout";
import ProfilePage from "../pages/ProfilePage";
import { api, hasAccessToken, setAccessToken } from "../shared/api";
import type { AuthResult, AuthUser } from "./types";

export default function AppRouter() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    if (!hasAccessToken()) { setAuthChecked(true); return; }
    api<AuthUser>("/auth/me")
      .then(setUser)
      .catch(() => setAccessToken(""))
      .finally(() => setAuthChecked(true));
  }, []);

  useEffect(() => {
    const expireSession = () => signOut();
    window.addEventListener("nexply:auth-expired", expireSession);
    return () => window.removeEventListener("nexply:auth-expired", expireSession);
  }, []);

  function completeAuthentication(result: AuthResult) {
    setAccessToken(result.access_token);
    setUser(result.user);
  }

  function signOut() {
    setAccessToken("");
    setUser(null);
    setAuthChecked(true);
  }

  if (!user) return <Auth onAuthenticated={completeAuthentication} checking={!authChecked} />;

  return <AppLayout user={user} onSignOut={signOut}><ProfilePage /></AppLayout>;
}
