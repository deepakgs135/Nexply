export type AuthResult = {
  access_token: string;
  user: { app_id: string; full_name: string; email: string };
};
export type Mode = "login" | "register" | "forgot";
export type RecoveryStep = "email" | "otp" | "password";
