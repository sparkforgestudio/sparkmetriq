"use client"

import { useEffect, useState } from "react"
import { ExportButton } from "@/components/ExportButton"
import { FilterBar } from "@/components/FilterBar"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { DataTable } from "@/components/DataTable"

type TunnelStats = {
  tunnel_id: string
  agency_name: string
  muse_name: string
  platforms: string[]
  total_posts: number
  success_rate: number
  avg_engagement: number
  conversion_rate: number
  revenue_per_fan: number
  updated_at: string
}

export default function TunnelsAnalyticsPage() {
  const [tunnels, setTunnels] = useState<TunnelStats[]>([])
  const [loading, setLoading] = useState(true)

  const [filters, setFilters] = useState({
    agency_id: "",
    muse_id: "",
    platform: "",
    start: "",
    end: "",
  })

  useEffect(() => {
    const query = new URLSearchParams(filters as any).toString()
    fetch(`/api/stats/tunnels?${query}`)
      .then((res) => res.json())
      .then((data) => {
        setTunnels(data.tunnels)
        setLoading(false)
      })
  }, [filters])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Analyse avancée des tunnels de vente</h1>

      <FilterBar filters={filters} setFilters={setFilters} />

      <Card className="p-4">
        {loading ? (
          <p>Chargement des données...</p>
        ) : (
          <DataTable
            headers={[
              "Tunnel",
              "Agence",
              "Muse",
              "Plateformes",
              "Posts",
              "Succès (%)",
              "Conv. (%)",
              "Revenue/fan",
              "MàJ",
              "Actions",
            ]}
            data={tunnels.map((item) => [
              item.tunnel_id.slice(0, 6),
              item.agency_name,
              item.muse_name,
              <div className="flex gap-1 flex-wrap">
                {item.platforms.map((p) => (
                  <Badge key={p}>{p}</Badge>
                ))}
              </div>,
              item.total_posts,
              `${item.success_rate.toFixed(1)}%`,
              `${item.conversion_rate.toFixed(1)}%`,
              `$${item.revenue_per_fan.toFixed(2)}`,
              new Date(item.updated_at).toLocaleDateString(),
              <ExportButton tunnelId={item.tunnel_id} />,
            ])}
          />
        )}
      </Card>
    </div>
  )
}
