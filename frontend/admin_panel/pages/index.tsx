'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

interface Task {
  _id: string;
  platform: string;
  type: string;
  caption: string;
  scheduled_at: string;
  status: string;
}

export default function DashboardPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const token = Cookies.get('token');

  const fetchTasks = async () => {
    if (!token) {
      router.push('/login');
      return;
    }

    const res = await fetch('http://localhost:8000/api/scheduler', {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (res.ok) {
      const data = await res.json();
      setTasks(data);
    } else {
      alert('Erreur lors du chargement des tâches');
    }

    setLoading(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Confirmer la suppression de cette tâche ?')) return;

    const res = await fetch(`http://localhost:8000/api/scheduler/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });

    if (res.ok) {
      alert('Tâche supprimée !');
      fetchTasks();
    } else {
      alert('Échec de la suppression');
    }
  };

  const handleLogout = () => {
    Cookies.remove('token');
    router.push('/login');
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  return (
    <div className="max-w-4xl mx-auto py-10 px-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">🛠️ Dashboard – Tâches programmées</h1>
        <div className="flex gap-4">
          <button
            onClick={() => router.push('/dashboard/create')}
            className="bg-blue-500 text-white px-4 py-2 rounded-xl hover:bg-blue-600"
          >
            ➕ Nouvelle tâche
          </button>
          <button
            onClick={handleLogout}
            className="bg-gray-300 px-4 py-2 rounded-xl hover:bg-gray-400"
          >
            🚪 Déconnexion
          </button>
        </div>
      </div>

      {loading ? (
        <p>Chargement des tâches...</p>
      ) : tasks.length === 0 ? (
        <p>Aucune tâche programmée.</p>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <div
              key={task._id}
              className="bg-white p-4 rounded-xl shadow-md border border-gray-200"
            >
              <p className="font-semibold text-gray-800">
                📱 {task.platform.toUpperCase()} – {task.type}
              </p>
              <p className="text-sm text-gray-600">{task.caption}</p>
              <p className="text-xs text-gray-500 mt-1">
                🕒 {new Date(task.scheduled_at).toLocaleString()}
              </p>
              <p className="text-xs mt-1 text-gray-400 italic">Statut : {task.status}</p>

              <div className="flex gap-4 mt-3">
                <button
                  onClick={() => router.push(`/dashboard/edit/${task._id}`)}
                  className="text-blue-600 hover:underline"
                >
                  ✏️ Modifier
                </button>
                <button
                  onClick={() => handleDelete(task._id)}
                  className="text-red-600 hover:underline"
                >
                  🗑️ Supprimer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
