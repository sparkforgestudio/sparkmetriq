import { useEffect, useState } from "react"

export function useSession() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const res = await fetch("/api/auth/session", {
          credentials: "include",
        })

        if (res.ok) {
          const data = await res.json()
          setUser(data.user)
        } else {
          setUser(null)
        }
      } catch (error) {
        console.error("Erreur lors de la récupération de la session", error)
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    fetchSession()
  }, [])

  return { user, loading }
}
// lib/logout.ts
export async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    localStorage.removeItem("token"); // ou supprimer les cookies si tu les utilises
    window.location.href = "/login";
  }
