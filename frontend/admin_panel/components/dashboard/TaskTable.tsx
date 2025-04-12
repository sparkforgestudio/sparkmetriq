// dashboard/scheduler/TaskTable.tsx
"use client";

import { useEffect, useState } from "react";
import axios from "@/lib/axios";

export default function TaskTable() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await axios.get("/api/scheduler");
        setTasks(response.data);
      } catch (error) {
        console.error("Erreur lors du chargement des tâches:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, []);

  if (loading) return <div>Chargement...</div>;

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm text-left">
        <thead>
          <tr className="bg-gray-200">
            <th className="p-2">Plateforme</th>
            <th className="p-2">Muse</th>
            <th className="p-2">Statut</th>
            <th className="p-2">Programmée pour</th>
            <th className="p-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task._id} className="border-b">
              <td className="p-2">{task.platform}</td>
              <td className="p-2">{task.muse_id}</td>
              <td className="p-2">{task.status}</td>
              <td className="p-2">
                {new Date(task.scheduled_at).toLocaleString()}
              </td>
              <td className="p-2 text-blue-500">Voir</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
