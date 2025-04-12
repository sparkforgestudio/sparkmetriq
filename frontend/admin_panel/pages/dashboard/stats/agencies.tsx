"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"

export default function AgenciesStats() {
  const [agencies, setAgencies] = useState<any[]>([])

  useEffect(() => {
    fetch("/api/stats/agencies")
      .then((res) => res.json())
      .then((data) => setAgencies(data))
  }, [])

  const exportCSV = () => {
    const headers = ["Agency", "Total Posts", "Total Errors", "Success Rate"]
    const rows = agencies.map((a) => [
      a.agency_id,
      a.total_posts,
      a.total_errors,
      a.success_rate,
    ])
    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n")

    const blob = new Blob([csv], { type: "text/csv" })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "agency_stats.csv"
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Statistiques par agence</h1>
        <button onClick={exportCSV} className="bg-blue-600 text-white px-4 py-2 rounded">
          Exporter en CSV
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agencies.map((agency) => (
          <Card key={agency.agency_id}>
            <h3 className="text-lg font-semibold">{agency.agency_id}</h3>
            <p>Total de posts : {agency.total_posts}</p>
            <p className="text-green-600">Succès : {agency.success_rate.toFixed(1)}%</p>
            <p className="text-red-600">Erreurs : {agency.total_errors}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
