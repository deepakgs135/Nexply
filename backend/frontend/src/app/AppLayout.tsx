import type { ReactNode } from "react";
import { ChevronDown, LockKeyhole, ShieldCheck, UserRound } from "lucide-react";
import type { AuthUser } from "./types";

export default function AppLayout({
  user, onSignOut, children,
}: {
  user: AuthUser;
  onSignOut: () => void;
  children: ReactNode;
}) {
  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="NEXPLY home"><span className="brand-symbol">N</span><span className="brand-word">NEXPLY<small>AI</small></span></a>
      <button className="workspace-select"><span className="workspace-monogram">T</span><span><small>WORKSPACE</small><strong>Talent operations</strong></span><ChevronDown size={15} /></button>
      <div className="side-bottom"><nav className="side-nav side-bottom-nav" aria-label="Workspace"><a className="nav-link selected" href="#profile" aria-label="Profile" title="Profile"><UserRound size={17} /><span>Profile</span><i /></a></nav><div className="privacy-card"><ShieldCheck size={17} /><strong>Designed for responsible review</strong><p>Your latest candidate profile stays private and reviewable.</p></div><div className="member-card"><span className="member-avatar">{user.full_name.slice(0, 1).toUpperCase()}</span><span><strong>{user.full_name}</strong><small>{user.email}</small></span><button onClick={onSignOut} aria-label="Sign out" title="Sign out">↗</button></div></div>
    </aside>
    <main className="main-content" id="profile">
      <header className="topbar"><div className="breadcrumbs">Workspace <span>/</span> <strong>Profile</strong></div><div className="topbar-actions"><span className="privacy-status"><LockKeyhole size={13} /> Private workspace</span><span className="user-dot">{user.full_name.slice(0, 1).toUpperCase()}</span><button className="signout-button" onClick={onSignOut}>Sign out</button></div></header>
      {children}
    </main>
  </div>;
}
