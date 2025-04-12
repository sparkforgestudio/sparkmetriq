// admin_panel/lib/api.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const fetchScheduledTasks = async () => {
  const res = await fetch(`${BASE_URL}/scheduler`);
  return res.json();
};

export const deleteScheduledTask = async (id: string) => {
  const res = await fetch(`${BASE_URL}/scheduler/${id}`, {
    method: 'DELETE',
  });
  return res.json();
};
