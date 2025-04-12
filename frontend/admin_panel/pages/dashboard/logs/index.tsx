import { useEffect, useState } from "react";
import axios from "@/lib/axios";
import { useSession } from "@/hooks/useSession";
import { Card } from "@/components/ui/card";

type LogItem = {
  platform: string;
  muse_id?: string;
  status: string;
  message: string;
  timestamp: string;
  metadata?: Record<string, any>;
};

export default function LogsDashboard() {
  const { session } = useSession();
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [loading, setLoading] = useState(true);

  const agencyId = session?.user?.agency_id || "default-agency";

  useEffect(() => {
    if (!session?.token) return;
    const fetchLogs = async () => {
      try {
        const res = await axios.get("/api/logs", {
          params: { agency_id: agencyId, limit: 50 },
          headers: {
            Authorization: `Bearer ${session.token}`,
          },
        });
        setLogs(res.data);
      } catch (err) {
        console.error("Erreur lors du chargement des logs", err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [session]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">📊 Logs d’exécution</h1>

      {loading ? (
        <p>Chargement des logs...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {logs.map((log, idx) => (
            <Card key={idx} className="p-4 border shadow rounded-xl">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-700">
                  {log.platform.toUpperCase()} – {log.status.toUpperCase()}
                </span>
                <span
                  className={`text-xs font-semibold px-2 py-1 rounded ${
                    log.status === "success"
                      ? "bg-green-100 text-green-700"
                      : log.status === "error"
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {log.status}
                </span>
              </div>
              <p className="text-sm mb-1">{log.message}</p>
              <p className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleString()}</p>

              {log.metadata && Object.keys(log.metadata).length > 0 && (
                <pre className="mt-2 bg-gray-50 text-xs p-2 rounded text-gray-700 overflow-x-auto">
                  {JSON.stringify(log.metadata, null, 2)}
                </pre>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
