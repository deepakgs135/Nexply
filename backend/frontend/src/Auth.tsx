import { useState, type FormEvent } from "react";
import { AuthView } from "./AuthView";
import type { AuthResult, Mode, RecoveryStep } from "./authTypes";
const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function Auth({ onAuthenticated, checking }: {
  onAuthenticated: (result: AuthResult) => void;
  checking: boolean;
}) {
  const [mode, setMode] = useState<Mode>("login");
  const [recoveryStep, setRecoveryStep] = useState<RecoveryStep>("email");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function switchMode(next: Mode) {
    setMode(next);
    setRecoveryStep("email");
    setError("");
    setNotice("");
  }

  async function request(path: string, body: Record<string, string>) {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || "Unable to complete this request. Please try again.");
    return result;
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      if (mode === "register") {
        if (password !== confirmPassword) throw new Error("Passwords do not match.");
        const result = await request("/auth/register", { full_name: fullName, email, password, confirm_password: confirmPassword });
        onAuthenticated(result as AuthResult);
      } else if (mode === "login") {
        const result = await request("/auth/login", { email, password });
        onAuthenticated(result as AuthResult);
      } else if (recoveryStep === "email") {
        await request("/auth/password-reset/request", { email });
        setRecoveryStep("otp");
        setNotice("If an active account exists for this email, a verification code has been sent.");
      } else if (recoveryStep === "otp") {
        const result = await request("/auth/password-reset/verify", { email, otp });
        setResetToken(result.reset_token);
        setRecoveryStep("password");
        setNotice("Email verified. Choose a new password.");
      } else {
        if (password !== confirmPassword) throw new Error("Passwords do not match.");
        await request("/auth/password-reset/complete", {
          email, reset_token: resetToken, new_password: password, confirm_password: confirmPassword,
        });
        switchMode("login");
        setNotice("Password updated. Sign in with your new password.");
        setPassword("");
        setConfirmPassword("");
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to complete this request. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  const title = checking ? "Checking your session" : mode === "register" ? "Create your account" : mode === "forgot" ? "Reset your password" : "Welcome back";
  const description = checking ? "Verifying your account securelyâ€¦" : mode === "register"
    ? "Set up your private candidate workspace."
    : mode === "forgot"
      ? recoveryStep === "email" ? "Weâ€™ll send a one-time code to your account email." : recoveryStep === "otp" ? `Enter the six-digit code sent to ${email}.` : "Your email is verified. Set a new password below."
      : "Sign in to continue to your candidate workspace.";

  return <AuthView
    checking={checking} title={title} description={description} mode={mode} recoveryStep={recoveryStep}
    fullName={fullName} setFullName={setFullName} email={email} setEmail={setEmail}
    password={password} setPassword={setPassword} confirmPassword={confirmPassword} setConfirmPassword={setConfirmPassword}
    otp={otp} setOtp={setOtp} showPassword={showPassword} setShowPassword={setShowPassword}
    busy={busy} error={error} notice={notice} onSwitchMode={switchMode} onSubmit={submit}
    onBack={() => { setError(""); setNotice(""); setRecoveryStep(recoveryStep === "password" ? "otp" : "email"); setResetToken(""); }}
  />;
}
