"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

type Stats = {
  platform: string
  total_posts: number
  total_errors: number
  success_rate: number
}

type TimelinePoint = {
  date: string
  posts: number
}

export default function StatsDashboard() {
  const [globalStats, setGlobalStats] = useState<Stats[]>([])
  const [timelineData, setTimelineData] = useState<TimelinePoint[]>([])

  useEffect(() => {
    // 🚀 Appels à l’API backend
    fetch("/api/stats/overview")
      .then((res) => res.json())
      .then((data) => setGlobalStats(data.stats))

    fetch("/api/stats/timeline")
      .then((res) => res.json())
      .then((data) => setTimelineData(data.timeline))
  }, [])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Statistiques de publication</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {globalStats.map((item) => (
          <Card key={item.platform}>
            <h3 className="text-lg font-semibold capitalize">{item.platform}</h3>
            <p className="mt-2 text-sm">Total posts : {item.total_posts}</p>
            <p className="text-sm text-green-600">Succès : {item.success_rate.toFixed(1)}%</p>
            <p className="text-sm text-red-500">Erreurs : {item.total_errors}</p>
          </Card>
        ))}
      </div>

      <Card>
        <h2 className="text-lg font-bold mb-4">Activité des 30 derniers jours</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timelineData}>
              <Line type="monotone" dataKey="posts" stroke="#4f46e5" strokeWidth={2} />
              <CartesianGrid stroke="#e5e7eb" strokeDasharray="5 5" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}
