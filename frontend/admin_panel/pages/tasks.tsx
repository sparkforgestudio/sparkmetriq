// frontend/admin_panel/pages/tasks.tsx
'use client';

import { useEffect, useState } from 'react';
import { getTasks } from '../lib/api';

interface Task {
  _id: string;
  agency_id: string;
  muse_id: string;
  platform: string;
  type: string;
  scheduled_at: string;
  status: string;
  caption?: string;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    getTasks().then(setTasks);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <h1 className="text-2xl font-bold mb-4">Tâches Planifiées</h1>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white rounded shadow">
          <thead>
            <tr>
              <th className="py-2 px-4 border">Platform</th>
              <th className="py-2 px-4 border">Muse</th>
              <th className="py-2 px-4 border">Type</th>
              <th className="py-2 px-4 border">Status</th>
              <th className="py-2 px-4 border">Date</th>
              <th className="py-2 px-4 border">Actions</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map(task => (
              <tr key={task._id} className="text-sm">
                <td className="py-2 px-4 border">{task.platform}</td>
                <td className="py-2 px-4 border">{task.muse_id}</td>
                <td className="py-2 px-4 border">{task.type}</td>
                <td className="py-2 px-4 border">{task.status}</td>
                <td className="py-2 px-4 border">{new Date(task.scheduled_at).toLocaleString()}</td>
                <td className="py-2 px-4 border">-</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
