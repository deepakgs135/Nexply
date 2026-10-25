import type { ReactNode } from "react";
import { Activity, Clock3, ChevronDown, FileText, LayoutDashboard, LockKeyhole, ShieldCheck } from "lucide-react";
import type { AppPage, AuthUser } from "./types";

export default function AppLayout({
  user, activePage, onPageChange, onSignOut, children,
}: {
  user: AuthUser;
  activePage: AppPage;
  onPageChange: (page: AppPage) => void;
  onSignOut: () => void;
  children: ReactNode;
}) {
  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="NEXPLY home"><span className="brand-symbol">N</span><span className="brand-word">NEXPLY<small>AI</small></span></a>
      <button className="workspace-select"><span className="workspace-monogram">T</span><span><small>WORKSPACE</small><strong>Talent operations</strong></span><ChevronDown size={15} /></button>
      <div className="side-caption">WORKSPACE</div>
      <nav className="side-nav" aria-label="Workspace">
        <a className={`nav-link ${activePage === "workspace" ? "selected" : ""}`} href="#workspace" onClick={() => onPageChange("workspace")}><LayoutDashboard size={17} /><span>Candidate intelligence</span>{activePage === "workspace" && <i />}</a>
        <a className={`nav-link ${activePage === "history" ? "selected" : ""}`} href="#history" onClick={() => onPageChange("history")}><Clock3 size={17} /><span>Resume History</span>{activePage === "history" && <i />}</a>
        <a className="nav-link muted" aria-disabled="true"><FileText size={17} /><span>Job descriptions</span><em>SOON</em></a>
        <a className="nav-link muted" aria-disabled="true"><Activity size={17} /><span>Activity</span><em>SOON</em></a>
      </nav>
      <div className="side-bottom"><div className="privacy-card"><ShieldCheck size={17} /><strong>Designed for responsible review</strong><p>Structured candidate information stays clear and reviewable.</p></div><div className="member-card"><span className="member-avatar">{user.full_name.slice(0, 1).toUpperCase()}</span><span><strong>{user.full_name}</strong><small>{user.email}</small></span><button onClick={onSignOut} aria-label="Sign out" title="Sign out">↗</button></div></div>
    </aside>
    <main className="main-content" id="workspace">
      <header className="topbar"><div className="breadcrumbs">Workspace <span>/</span> <strong>{activePage === "history" ? "Resume History" : "Candidate intelligence"}</strong></div><div className="topbar-actions"><span className="privacy-status"><LockKeyhole size={13} /> Private workspace</span><span className="user-dot">{user.full_name.slice(0, 1).toUpperCase()}</span><button className="signout-button" onClick={onSignOut}>Sign out</button></div></header>
      {children}
    </main>
  </div>;
}
