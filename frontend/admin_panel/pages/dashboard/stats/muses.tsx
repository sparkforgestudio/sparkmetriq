"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"

export default function MusesStats() {
  const [muses, setMuses] = useState<any[]>([])

  useEffect(() => {
    fetch("/api/stats/muses")
      .then((res) => res.json())
      .then((data) => setMuses(data))
  }, [])

  const exportCSV = () => {
    const headers = ["Muse", "Agency", "Total Posts", "Total Errors", "Success Rate"]
    const rows = muses.map((m) => [
      m.muse_id,
      m.agency_id,
      m.total_posts,
      m.total_errors,
      m.success_rate,
    ])
    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n")

    const blob = new Blob([csv], { type: "text/csv" })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "muse_stats.csv"
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Statistiques par muse</h1>
        <button onClick={exportCSV} className="bg-blue-600 text-white px-4 py-2 rounded">
          Exporter en CSV
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {muses.map((muse) => (
          <Card key={muse.muse_id}>
            <h3 className="text-lg font-semibold">{muse.muse_id}</h3>
            <p>Agence : {muse.agency_id}</p>
            <p>Total de posts : {muse.total_posts}</p>
            <p className="text-green-600">Succès : {muse.success_rate.toFixed(1)}%</p>
            <p className="text-red-600">Erreurs : {muse.total_errors}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
