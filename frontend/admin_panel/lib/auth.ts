// frontend/admin_panel/lib/auth.ts
/**
 * Utilitaire pour gérer l'authentification côté client.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface AuthUser {
  id: string;
  email: string;
  name?: string;
  picture?: string;
  org_id: string;
  is_admin: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user?: AuthUser;
}

/**
 * Récupère le token d'accès depuis localStorage.
 */
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

/**
 * Récupère les informations utilisateur depuis localStorage.
 */
export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const userStr = localStorage.getItem("user");
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

/**
 * Stocke les informations d'authentification.
 */
export function setAuthData(response: AuthResponse): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("access_token", response.access_token);
  localStorage.setItem("token_type", response.token_type || "bearer");
  if (response.user) {
    localStorage.setItem("user", JSON.stringify(response.user));
  }
}

/**
 * Supprime les informations d'authentification.
 */
export function clearAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("token_type");
  localStorage.removeItem("user");
}

/**
 * Vérifie si l'utilisateur est authentifié.
 */
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

/**
 * Connexion avec email/password.
 */
export async function loginWithEmail(
  email: string,
  password: string
): Promise<AuthResponse> {
  const formData = new URLSearchParams({
    username: email,
    password: password,
  });

  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Échec de la connexion");
  }

  return await response.json();
}

/**
 * Connexion avec Google OAuth.
 */
export async function loginWithGoogle(
  idToken: string,
  orgId?: string
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/google/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      token: idToken,
      org_id: orgId,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Échec de la connexion Google");
  }

  return await response.json();
}

/**
 * Inscription avec email/password.
 */
export async function registerWithEmail(
  email: string,
  password: string,
  isAdmin: boolean = false
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      is_admin: isAdmin,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Échec de l'inscription");
  }

  return await response.json();
}



