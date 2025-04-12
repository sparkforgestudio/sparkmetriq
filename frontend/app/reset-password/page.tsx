"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setMessage("Les mots de passe ne correspondent pas.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const res = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });

      const data = await res.json();
      if (res.ok) {
        setMessage("Mot de passe mis à jour avec succès. Redirection...");
        setTimeout(() => router.push("/login"), 2000);
      } else {
        setMessage(data.detail || "Une erreur est survenue.");
      }
    } catch (error) {
      setMessage("Erreur de connexion au serveur.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="w-full max-w-md bg-white p-6 rounded-lg shadow-lg">
        <h2 className="text-2xl font-semibold text-center text-gray-700">
          Réinitialiser le mot de passe
        </h2>

        <form className="mt-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-600">Nouveau mot de passe</label>
            <input
              type="password"
              className="w-full px-4 py-2 mt-2 border rounded-lg focus:ring focus:ring-blue-300"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="mt-3">
            <label className="block text-sm font-medium text-gray-600">Confirmer le mot de passe</label>
            <input
              type="password"
              className="w-full px-4 py-2 mt-2 border rounded-lg focus:ring focus:ring-blue-300"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          {message && <p className="mt-2 text-sm text-red-500">{message}</p>}

          <button
            type="submit"
            className="w-full mt-4 px-4 py-2 text-white bg-blue-500 rounded-lg hover:bg-blue-600 transition"
            disabled={loading}
          >
            {loading ? "Mise à jour..." : "Mettre à jour"}
          </button>
        </form>
      </div>
    </div>
  );
}
