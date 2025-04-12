"use client"

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function FilterBar({
  filters,
  setFilters,
}: {
  filters: any
  setFilters: (val: any) => void
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
      {["agency_id", "muse_id", "platform", "start", "end"].map((field) => (
        <div key={field}>
          <Label>{field.replace("_", " ").toUpperCase()}</Label>
          <Input
            type={field.includes("date") ? "date" : "text"}
            value={filters[field]}
            onChange={(e) => setFilters({ ...filters, [field]: e.target.value })}
          />
        </div>
      ))}
    </div>
  )
}
