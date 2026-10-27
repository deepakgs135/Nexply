import { type FormEvent } from "react";
import { ArrowLeft, ArrowRight, Eye, EyeOff, LockKeyhole, Mail, ShieldCheck, UserRound } from "lucide-react";
import type { Mode, RecoveryStep } from "./authTypes"

type AuthViewProps = {
  checking: boolean; title: string; description: string; mode: Mode; recoveryStep: RecoveryStep;
  fullName: string; setFullName: (value: string) => void; email: string; setEmail: (value: string) => void;
  password: string; setPassword: (value: string) => void; confirmPassword: string; setConfirmPassword: (value: string) => void;
  otp: string; setOtp: (value: string) => void; showPassword: boolean; setShowPassword: (value: boolean) => void;
  busy: boolean; error: string; notice: string; onSwitchMode: (mode: Mode) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void; onBack: () => void;
};

export function AuthView({ checking, title, description, mode, recoveryStep, fullName, setFullName, email, setEmail, password, setPassword, confirmPassword, setConfirmPassword, otp, setOtp, showPassword, setShowPassword, busy, error, notice, onSwitchMode, onSubmit, onBack }: AuthViewProps) {
  return <main className="auth-page">
    <section className="auth-aside">
      <a className="auth-brand" href="/"><span className="brand-symbol">N</span><span>NEXPLY<small>AI</small></span></a>
      <div className="auth-aside-copy">
        <span className="auth-eyebrow"><i /> TALENT INTELLIGENCE</span>
        <h1>Make every candidate detail count.</h1>
        <p>Review complete, structured profiles alongside their original resumes in one private workspace.</p>
      </div>
      <div className="auth-assurance"><ShieldCheck size={16} /><span><strong>Private by design</strong><small>Your workspace is tied to your account.</small></span></div>
      <span className="auth-aside-foot">NEXPLY AI | CANDIDATE WORKSPACE</span>
    </section>
    <section className="auth-main">
      <div className="auth-card">
        <div className="auth-mobile-brand"><span className="brand-symbol">N</span><strong>NEXPLY AI</strong></div>
        <span className="auth-label">SECURE WORKSPACE ACCESS</span>
        <h2>{title}</h2>
        <p className="auth-description">{description}</p>
        {!checking && <>
          {mode !== "forgot" ? <div className="auth-tabs"><button type="button" className={mode === "login" ? "active" : ""} onClick={() => onSwitchMode("login")}>Sign in</button><button type="button" className={mode === "register" ? "active" : ""} onClick={() => onSwitchMode("register")}>Create account</button></div> : <div className="auth-recovery-progress"><span className={recoveryStep === "email" ? "active" : "done"}>Email</span><i /><span className={recoveryStep === "otp" ? "active" : recoveryStep === "password" ? "done" : ""}>Verify</span><i /><span className={recoveryStep === "password" ? "active" : ""}>New password</span></div>}
          <form className="auth-form" onSubmit={onSubmit}>
            {mode === "register" && <label>Full name<span className="auth-input"><UserRound size={16} /><input autoComplete="name" required maxLength={120} value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Your full name" /></span></label>}
            {(mode !== "forgot" || recoveryStep === "email" || recoveryStep === "otp" || recoveryStep === "password") && <label>Email address<span className="auth-input"><span className="auth-at">@</span><input type="email" autoComplete="email" required maxLength={255} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" readOnly={mode === "forgot" && recoveryStep !== "email"} /></span></label>}
            {mode === "forgot" && recoveryStep === "otp" && <label>Verification code<span className="auth-input"><Mail size={15} /><input inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required value={otp} onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))} placeholder="Enter 6-digit code" /></span></label>}
            {(mode === "login" || mode === "register" || (mode === "forgot" && recoveryStep === "password")) && <>
              <label>{mode === "forgot" ? "New password" : "Password"}<span className="auth-input"><LockKeyhole size={15} /><input type={showPassword ? "text" : "password"} autoComplete={mode === "login" ? "current-password" : "new-password"} required minLength={mode === "login" ? 1 : 12} maxLength={256} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === "login" ? "Enter your password" : "At least 12 characters"} /><button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={15} /> : <Eye size={15} />}</button></span></label>
              {(mode === "register" || (mode === "forgot" && recoveryStep === "password")) && <label>Confirm password<span className="auth-input"><LockKeyhole size={15} /><input type={showPassword ? "text" : "password"} autoComplete="new-password" required minLength={12} maxLength={256} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Re-enter your password" /></span></label>}
            </>}
            {mode === "register" && <small className="password-hint">Use at least 12 characters for a stronger password.</small>}
            {mode === "login" && <button type="button" className="auth-forgot-link" onClick={() => onSwitchMode("forgot")}>Forgot password?</button>}
            {error && <div className="auth-error" role="alert">{error}</div>}
            {notice && <div className="auth-notice" role="status">{notice}</div>}
            <button className="auth-submit" disabled={busy} type="submit">{busy ? "Please wait..." : mode === "register" ? "Create secure account" : mode === "login" ? "Sign in to NEXPLY" : recoveryStep === "email" ? "Send verification code" : recoveryStep === "otp" ? "Verify code" : "Update password"}<ArrowRight size={16} /></button>
            {mode === "forgot" && recoveryStep !== "email" && <button className="auth-back-link" type="button" onClick={onBack}> <ArrowLeft size={14} /> {recoveryStep === "password" ? "Back to code" : "Change email"}</button>}
          </form>
          <div className="auth-privacy"><ShieldCheck size={14} /><span>Passwords use Argon2id. Recovery codes expire after a short time and can only be used once.</span></div>
        </>}
        {checking && <div className="auth-checking"><span /> Verifying secure session</div>}
      </div>
      <footer className="auth-footer">Copyright 2026 NEXPLY AI <span>|</span> Secure candidate intelligence</footer>
    </section>
  </main>;
}
