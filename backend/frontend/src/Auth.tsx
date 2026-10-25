import { useState, type FormEvent } from "react";
import { ArrowRight, Eye, EyeOff, LockKeyhole, ShieldCheck, UserRound } from "lucide-react";

type AuthResult = {
  access_token: string;
  user: { app_id: string; full_name: string; email: string };
};

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function Auth({ onAuthenticated, checking }: {
  onAuthenticated: (result: AuthResult) => void;
  checking: boolean;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/auth/${mode === "register" ? "register" : "login"}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mode === "register" ? { full_name: fullName, email, password } : { email, password }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || "Unable to authenticate. Please try again.");
      onAuthenticated(body as AuthResult);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to authenticate. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="auth-page">
    <section className="auth-aside">
      <a className="auth-brand" href="/"><span className="brand-symbol">N</span><span>NEXPLY<small>AI</small></span></a>
      <div className="auth-aside-copy">
        <span className="auth-eyebrow"><i /> TALENT INTELLIGENCE</span>
        <h1>Make every candidate detail count.</h1>
        <p>Review complete, structured profiles alongside their original resumes in one private workspace.</p>
      </div>
      <div className="auth-assurance"><ShieldCheck size={16} /><span><strong>Private by design</strong><small>Your workspace is tied to your account.</small></span></div>
      <span className="auth-aside-foot">NEXPLY AI · CANDIDATE WORKSPACE</span>
    </section>
    <section className="auth-main">
      <div className="auth-card">
        <div className="auth-mobile-brand"><span className="brand-symbol">N</span><strong>NEXPLY AI</strong></div>
        <span className="auth-label">SECURE WORKSPACE ACCESS</span>
        <h2>{checking ? "Checking your session" : mode === "register" ? "Create your account" : "Welcome back"}</h2>
        <p className="auth-description">{checking ? "Verifying your account securely…" : mode === "register" ? "Set up your private candidate workspace." : "Sign in to continue to your candidate workspace."}</p>
        {!checking && <>
          <div className="auth-tabs"><button type="button" className={mode === "login" ? "active" : ""} onClick={() => { setMode("login"); setError(""); }}>Sign in</button><button type="button" className={mode === "register" ? "active" : ""} onClick={() => { setMode("register"); setError(""); }}>Create account</button></div>
          <form className="auth-form" onSubmit={submit}>
            {mode === "register" && <label>Full name<span className="auth-input"><UserRound size={16} /><input autoComplete="name" required maxLength={120} value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Your full name" /></span></label>}
            <label>Email address<span className="auth-input"><span className="auth-at">@</span><input type="email" autoComplete="email" required maxLength={255} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" /></span></label>
            <label>Password<span className="auth-input"><LockKeyhole size={15} /><input type={showPassword ? "text" : "password"} autoComplete={mode === "register" ? "new-password" : "current-password"} required minLength={mode === "register" ? 12 : 1} maxLength={256} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === "register" ? "At least 12 characters" : "Enter your password"} /><button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={15} /> : <Eye size={15} />}</button></span></label>
            {mode === "register" && <small className="password-hint">Use at least 12 characters for a stronger password.</small>}
            {error && <div className="auth-error" role="alert">{error}</div>}
            <button className="auth-submit" disabled={busy} type="submit">{busy ? "Please wait…" : mode === "register" ? "Create secure account" : "Sign in to NEXPLY"}<ArrowRight size={16} /></button>
          </form>
          <div className="auth-privacy"><ShieldCheck size={14} /><span>Passwords use Argon2id. Access tokens are signed, short lived, and never contain your password.</span></div>
        </>}
        {checking && <div className="auth-checking"><span /> Verifying secure session</div>}
      </div>
      <footer className="auth-footer">© 2026 NEXPLY AI <span>·</span> Secure candidate intelligence</footer>
    </section>
  </main>;
}
