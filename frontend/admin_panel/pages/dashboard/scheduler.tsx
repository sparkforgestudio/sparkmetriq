"use client"

import { useEffect, useState } from "react"
import axios from "@/lib/axios"
import { useSession } from "@/hooks/useSession"

type Task = {
  id: string
  agency_id: string
  muse_id: string
  platform: string
  type: string
  caption?: string
  scheduled_at: string
  status: string
  retries: number
}

export default function SchedulerPage() {
  const { user, loading: sessionLoading } = useSession()
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)

  const [filters, setFilters] = useState({
    agency_id: "",
    muse_id: "",
    status: ""
  })

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const query = new URLSearchParams({
          ...filters,
          skip: "0",
          limit: "50"
        })
        const res = await axios.get(`/api/scheduler/?${query.toString()}`, {
          withCredentials: true
        })
        setTasks(res.data)
      } catch (err) {
        console.error("Erreur lors de la récupération des tâches", err)
      } finally {
        setLoading(false)
      }
    }

    if (!sessionLoading && user) {
      fetchTasks()
    }
  }, [filters, user, sessionLoading])

  if (sessionLoading) return <div className="p-6">Chargement de la session...</div>
  if (!user) return <div className="p-6 text-red-500">Accès refusé. Connectez-vous d’abord.</div>

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">🗓️ Tâches planifiées</h2>

      <div className="flex flex-wrap gap-4 mb-6">
        <input
          type="text"
          placeholder="🔍 Agency ID"
          className="input input-bordered w-40"
          onChange={(e) => setFilters({ ...filters, agency_id: e.target.value })}
        />
        <input
          type="text"
          placeholder="🎭 Muse ID"
          className="input input-bordered w-40"
          onChange={(e) => setFilters({ ...filters, muse_id: e.target.value })}
        />
        <select
          className="select select-bordered w-40"
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
        >
          <option value="">Tous les statuts</option>
          <option value="pending">🟡 En attente</option>
          <option value="completed">🟢 Terminé</option>
          <option value="failed">🔴 Échec</option>
        </select>
      </div>

      {loading ? (
        <div>⏳ Chargement des tâches...</div>
      ) : tasks.length === 0 ? (
        <div>Aucune tâche planifiée.</div>
      ) : (
        <table className="table table-zebra w-full">
          <thead>
            <tr>
              <th>Date</th>
              <th>Plateforme</th>
              <th>Muse</th>
              <th>Agence</th>
              <th>Type</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id}>
                <td>{new Date(t.scheduled_at).toLocaleString()}</td>
                <td>{t.platform}</td>
                <td>{t.muse_id}</td>
                <td>{t.agency_id}</td>
                <td>{t.type}</td>
                <td>
                  {t.status === "pending" && <span className="badge badge-warning">🟡 En attente</span>}
                  {t.status === "completed" && <span className="badge badge-success">🟢 Terminé</span>}
                  {t.status === "failed" && <span className="badge badge-error">🔴 Échec</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
