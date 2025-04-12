import { useEffect, useState } from "react";
import { fetchScheduledTasks, deleteScheduledTask } from "../../lib/api";

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    fetchScheduledTasks().then(setTasks);
  }, []);

  const handleDelete = async (id: string) => {
    await deleteScheduledTask(id);
    setTasks(tasks.filter((t: any) => t._id !== id));
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Tâches Programmées</h1>
      <ul className="space-y-4">
        {tasks.map((task: any) => (
          <li key={task._id} className="p-4 bg-white shadow rounded">
            <div className="flex justify-between items-center">
              <span>{task.caption || "Sans description"}</span>
              <button
                onClick={() => handleDelete(task._id)}
                className="text-red-600 hover:underline"
              >
                Supprimer
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
