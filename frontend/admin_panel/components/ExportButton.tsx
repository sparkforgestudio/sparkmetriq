"use client"

import { Button } from "@/components/ui/button"

export function ExportButton({ tunnelId }: { tunnelId: string }) {
  const handleExport = () => {
    window.open(`/api/stats/tunnels/${tunnelId}/export`, "_blank")
  }

  return (
    <Button onClick={handleExport} variant="outline" size="sm">
      Export CSV
    </Button>
  )
}
