// frontend/admin_panel/lib/api.ts
/**
 * Client API pour les appels backend.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/**
 * Récupère le token d'accès depuis localStorage.
 */
function getAuthHeader(): { Authorization: string } | {} {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("access_token");
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

/**
 * Effectue une requête API authentifiée.
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith("http") ? endpoint : `${BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Erreur serveur" }));
    throw new Error(error.detail || `Erreur ${response.status}`);
  }

  return await response.json();
}

/**
 * Récupère les tâches programmées.
 */
export const fetchScheduledTasks = async () => {
  return apiRequest(`${BASE_URL}/api/scheduler/tasks`);
};

/**
 * Supprime une tâche programmée.
 */
export const deleteScheduledTask = async (id: string) => {
  return apiRequest(`${BASE_URL}/api/scheduler/${id}`, {
    method: "DELETE",
  });
};