"use client"

import { useRouter } from "next/navigation"
import { useSession } from "@/hooks/useSession"

export default function Header() {
  const { logout } = useSession()
  const router = useRouter()

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  return (
    <header className="flex justify-between items-center p-4 border-b bg-white shadow">
      <h1 className="text-xl font-bold">MuseMGM Admin Panel</h1>
      <button
        onClick={handleLogout}
        className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
      >
        Déconnexion
      </button>
    </header>
  )
}
