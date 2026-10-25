import { useEffect, useState } from "react";
import Auth from "../Auth";
import AppLayout from "./AppLayout";
import CandidateIntelligencePage from "../pages/CandidateIntelligencePage";
import ResumeHistoryPage from "../pages/ResumeHistoryPage";
import { api, hasAccessToken, setAccessToken } from "../shared/api";
import type { AppPage, AuthResult, AuthUser } from "./types";

export default function AppRouter() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [activePage, setActivePage] = useState<AppPage>("workspace");

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

  return <AppLayout user={user} activePage={activePage} onPageChange={setActivePage} onSignOut={signOut}>
    <div hidden={activePage !== "workspace"}>
      <CandidateIntelligencePage />
    </div>
    <div hidden={activePage !== "history"}>
      <ResumeHistoryPage request={api} enabled={activePage === "history"} />
    </div>
  </AppLayout>;
}
