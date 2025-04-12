# Vue Next.js : pages/dashboard/tunnels/index.tsx
"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Download } from "lucide-react"

export default function TunnelAnalysis() {
  const [agency, setAgency] = useState<string>("")
  const [muse, setMuse] = useState<string>("")
  const [tunnels, setTunnels] = useState<any[]>([])
  const [filters, setFilters] = useState({ period: "30d", platform: "all" })

  useEffect(() => {
    fetch("/api/stats/tunnels")
      .then(res => res.json())
      .then(data => setTunnels(data))
  }, [])

  const handleExport = () => {
    const query = new URLSearchParams({
      agency_id: agency,
      muse_id: muse,
      period: filters.period,
      platform: filters.platform,
    }).toString()
    window.open(`/api/stats/tunnels/export?${query}`, "_blank")
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Analyse des tunnels</h1>
        <Button onClick={handleExport}><Download className="mr-2 h-4 w-4" /> Exporter CSV</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <Label>Période</Label>
          <Select value={filters.period} onValueChange={(v) => setFilters(prev => ({ ...prev, period: v }))}>
            <SelectTrigger>
              <SelectValue placeholder="Période" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">7 jours</SelectItem>
              <SelectItem value="30d">30 jours</SelectItem>
              <SelectItem value="90d">3 mois</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Plateforme</Label>
          <Select value={filters.platform} onValueChange={(v) => setFilters(prev => ({ ...prev, platform: v }))}>
            <SelectTrigger>
              <SelectValue placeholder="Plateforme" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Toutes</SelectItem>
              <SelectItem value="instagram">Instagram</SelectItem>
              <SelectItem value="tiktok">TikTok</SelectItem>
              <SelectItem value="telegram">Telegram</SelectItem>
              <SelectItem value="onlyfans">OnlyFans</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Agence</Label>
          <Input value={agency} onChange={(e) => setAgency(e.target.value)} placeholder="agency_id" />
        </div>

        <div>
          <Label>Muse</Label>
          <Input value={muse} onChange={(e) => setMuse(e.target.value)} placeholder="muse_id" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        {tunnels.map((t, idx) => (
          <Card key={idx} className="p-4 space-y-2">
            <h3 className="font-semibold text-lg">{t.name || t.id}</h3>
            <p>Agence: {t.agency_id}</p>
            <p>Muse: {t.muse_id}</p>
            <p>Plateformes: {t.platforms.join(", ")}</p>
            <p className="text-green-600">Taux de conversion : {t.conversion_rate}%</p>
            <p className="text-gray-500 text-sm">Dernière activité : {t.last_active}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
