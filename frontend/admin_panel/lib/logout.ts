export async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    localStorage.removeItem("token"); // ou token dans un cookie sécurisé
  }
  