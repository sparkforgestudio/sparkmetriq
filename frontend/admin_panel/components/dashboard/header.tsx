"use client";

import { logout } from "@/lib/logout";
import { useSession } from "@/hooks/useSession";
import { useRouter } from "next/navigation";

export default function Header() {
  const { user, loading } = useSession();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <header className="bg-white border-b shadow-sm px-6 py-4 flex justify-between items-center">
      <h1 className="text-xl font-semibold text-gray-800">MuseMGM Panel</h1>
      <div className="flex items-center gap-4">
        {!loading && user && (
          <span className="text-gray-600 text-sm">
            Connecté en tant que <strong>{user.email}</strong>
          </span>
        )}
        <button
          onClick={handleLogout}
          className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
        >
          Se déconnecter
        </button>
      </div>
    </header>
  );
}
