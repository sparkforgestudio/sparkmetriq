import { useEffect, useState } from "react";
import { useRouter } from "next/router";

interface ScheduledTask {
  id: string;
  platform: string;
  caption: string;
  scheduled_at: string;
  status: string;
  muse_id: string;
}

export default function DashboardPage() {
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const fetchTasks = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/scheduler/tasks", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Erreur lors du chargement");

      const data = await response.json();
      setTasks(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) router.push("/login");
    else fetchTasks();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    router.push("/login");
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Confirmer la suppression ?")) return;

    try {
      const response = await fetch(`http://localhost:8000/api/scheduler/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        setTasks((prev) => prev.filter((task) => task.id !== id));
      } else {
        alert("Erreur lors de la suppression");
      }
    } catch (err) {
      console.error(err);
      alert("Erreur technique");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">🎛 Panel de gestion</h1>
        <div className="flex gap-3">
          <button
            onClick={() => router.push("/dashboard/create")}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
          >
            + Nouvelle tâche
          </button>
          <button
            onClick={handleLogout}
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
          >
            Déconnexion
          </button>
        </div>
      </div>

      {loading ? (
        <p>Chargement des tâches...</p>
      ) : (
        <div className="bg-white rounded-xl shadow p-4 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="p-2">Plateforme</th>
                <th className="p-2">Muse</th>
                <th className="p-2">Caption</th>
                <th className="p-2">Date</th>
                <th className="p-2">Statut</th>
                <th className="p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id} className="border-b hover:bg-gray-50">
                  <td className="p-2">{task.platform}</td>
                  <td className="p-2">{task.muse_id}</td>
                  <td className="p-2">{task.caption || "-"}</td>
                  <td className="p-2">{new Date(task.scheduled_at).toLocaleString()}</td>
                  <td className="p-2">{task.status}</td>
                  <td className="p-2 space-x-2">
                    <button
                      className="text-sm text-red-500 hover:underline"
                      onClick={() => handleDelete(task.id)}
                    >
                      Supprimer
                    </button>
                    {/* Ajoute plus tard un bouton "Modifier" si besoin */}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {tasks.length === 0 && <p className="text-gray-500 mt-4">Aucune tâche trouvée.</p>}
        </div>
      )}
    </div>
  );
}
