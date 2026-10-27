export type AuthUser = {
  app_id: string;
  full_name: string;
  email: string;
};

export type AuthResult = {
  access_token: string;
  user: AuthUser;
};
