import { useEffect, useState } from "react";
import { useRouter } from "next/router";

export default function EditTaskPage() {
  const router = useRouter();
  const { id } = router.query;

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const [task, setTask] = useState<any>(null);

  useEffect(() => {
    if (id && token) {
      fetch(`http://localhost:8000/api/scheduler/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => res.json())
        .then(setTask);
    }
  }, [id, token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const updatedTask = {
      ...task,
      scheduled_at: new Date(task.scheduled_at).toISOString(),
    };

    const res = await fetch(`http://localhost:8000/api/scheduler/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(updatedTask),
    });

    if (res.ok) {
      router.push("/dashboard");
    } else {
      alert("Erreur lors de la mise à jour.");
    }
  };

  if (!task) return <div className="p-6 text-gray-500">Chargement...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-xl mx-auto bg-white p-6 rounded-xl shadow">
        <h1 className="text-xl font-bold mb-4">✏️ Modifier la tâche</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium">Plateforme</label>
            <select
              value={task.platform}
              onChange={(e) => setTask({ ...task, platform: e.target.value })}
              className="w-full mt-1 border p-2 rounded"
            >
              <option value="instagram">Instagram</option>
              <option value="tiktok">TikTok</option>
              <option value="threads">Threads</option>
              <option value="reddit">Reddit</option>
              <option value="twitter">Twitter</option>
              <option value="telegram">Telegram</option>
              <option value="snapchat">Snapchat</option>
              <option value="facebook">Facebook</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium">Type</label>
            <select
              value={task.type}
              onChange={(e) => setTask({ ...task, type: e.target.value })}
              className="w-full mt-1 border p-2 rounded"
            >
              <option value="image">Image</option>
              <option value="video">Vidéo</option>
              <option value="carousel">Carousel</option>
              <option value="story">Story</option>
              <option value="reel">Reel</option>
              <option value="short">Short</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium">URL du média</label>
            <input
              type="url"
              value={task.media?.[0]?.url || ""}
              onChange={(e) =>
                setTask({ ...task, media: [{ type: task.type, url: e.target.value }] })
              }
              className="w-full mt-1 border p-2 rounded"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Légende</label>
            <textarea
              value={task.caption}
              onChange={(e) => setTask({ ...task, caption: e.target.value })}
              className="w-full mt-1 border p-2 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Date prévue</label>
            <input
              type="datetime-local"
              value={task.scheduled_at?.substring(0, 16)}
              onChange={(e) =>
                setTask({ ...task, scheduled_at: new Date(e.target.value).toISOString() })
              }
              className="w-full mt-1 border p-2 rounded"
              required
            />
          </div>

          <button
            type="submit"
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
          >
            ✅ Mettre à jour
          </button>
        </form>
      </div>
    </div>
  );
}
