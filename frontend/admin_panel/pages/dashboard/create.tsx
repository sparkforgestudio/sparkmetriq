import { useState } from "react";
import { useRouter } from "next/router";

export default function CreateTaskPage() {
  const router = useRouter();

  const [platform, setPlatform] = useState("instagram");
  const [caption, setCaption] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [mediaUrl, setMediaUrl] = useState("");
  const [type, setType] = useState("image");

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload = {
      agency_id: "agency001",
      muse_id: "muse001",
      platform,
      type,
      media: [{ type, url: mediaUrl }],
      caption,
      scheduled_at: new Date(scheduledAt).toISOString(),
      tags: [],
      language: "fr",
      is_sensitive: false,
    };

    const res = await fetch("http://localhost:8000/api/scheduler/create", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      router.push("/dashboard");
    } else {
      alert("Erreur lors de la création.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-xl mx-auto bg-white p-6 rounded-xl shadow">
        <h1 className="text-xl font-bold mb-4">🗓 Nouvelle tâche planifiée</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium">Plateforme</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
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
            <label className="block text-sm font-medium">Type de contenu</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
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
            <label className="block text-sm font-medium">Lien du média</label>
            <input
              type="url"
              value={mediaUrl}
              onChange={(e) => setMediaUrl(e.target.value)}
              className="w-full mt-1 border p-2 rounded"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Légende</label>
            <textarea
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              className="w-full mt-1 border p-2 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Date de publication</label>
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="w-full mt-1 border p-2 rounded"
              required
            />
          </div>

          <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
            Créer la tâche
          </button>
        </form>
      </div>
    </div>
  );
}
