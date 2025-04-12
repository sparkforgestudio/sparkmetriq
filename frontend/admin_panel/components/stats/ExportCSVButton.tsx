"use client"

import { Button } from "@/components/ui/button"

type ExportProps = {
  entity: "agencies" | "muses"
}

export function ExportCSVButton({ entity }: ExportProps) {
  const handleExport = () => {
    const url = `/api/stats/export?entity=${entity}`
    window.open(url, "_blank")
  }

  return (
    <Button variant="outline" onClick={handleExport}>
      📤 Exporter CSV
    </Button>
  )
}
