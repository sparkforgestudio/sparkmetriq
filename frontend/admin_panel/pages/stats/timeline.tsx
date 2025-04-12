"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { format } from "date-fns"
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts"
import { DownloadIcon } from "lucide-react"

type TimelinePoint = {
  date: string
  posts: number
  success_rate: number
  errors: number
}

export default function TimelineStatsPage() {
  const [timelineData, setTimelineData] = useState<TimelinePoint[]>([])
  const [agencyId, setAgencyId] = useState("")
  const [museId, setMuseId] = useState("")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")

  const fetchData = async () => {
    let url = `/api/stats/timeline?`
    if (agencyId) url += `agency_id=${agencyId}&`
    if (museId) url += `muse_id=${museId}&`
    if (startDate) url += `start_date=${startDate}&`
    if (endDate) url += `end_date=${endDate}&`

    const res = await fetch(url)
    const json = await res.json()
    setTimelineData(json.timeline)
  }

  const exportToCSV = () => {
    const headers = ["Date", "Posts", "Success Rate (%)", "Errors"]
    const rows = timelineData.map((d) => [
      d.date,
      d.posts,
      d.success_rate,
      d.errors,
    ])
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers, ...rows]
        .map((e) => e.join(","))
        .join("\n")
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement("a")
    link.setAttribute("href", encodedUri)
    link.setAttribute("download", `timeline_stats_${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Analyse Chronologique</h1>

      <Card className="p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <Label htmlFor="agencyId">Agence ID</Label>
            <Input
              id="agencyId"
              value={agencyId}
              onChange={(e) => setAgencyId(e.target.value)}
              placeholder="agency001"
            />
          </div>

          <div>
            <Label htmlFor="museId">Muse ID</Label>
            <Input
              id="museId"
              value={museId}
              onChange={(e) => setMuseId(e.target.value)}
              placeholder="muse001"
            />
          </div>

          <div>
            <Label htmlFor="startDate">Date début</Label>
            <Input
              id="startDate"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div>
            <Label htmlFor="endDate">Date fin</Label>
            <Input
              id="endDate"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
        </div>

        <div className="flex justify-between items-center">
          <Button onClick={fetchData}>🔍 Appliquer les filtres</Button>
          <Button onClick={exportToCSV} variant="outline">
            <DownloadIcon className="w-4 h-4 mr-2" /> Export CSV
          </Button>
        </div>
      </Card>

      <Card className="p-4">
        <h2 className="text-lg font-semibold mb-2">Activité quotidienne</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="posts" stroke="#1e40af" />
              <Line type="monotone" dataKey="success_rate" stroke="#22c55e" />
              <Line type="monotone" dataKey="errors" stroke="#ef4444" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}
