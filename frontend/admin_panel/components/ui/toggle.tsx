import { Switch } from "@headlessui/react"
import { useState } from "react"

type ToggleProps = {
  enabled: boolean
  setEnabled: (value: boolean) => void
  label?: string
}

export function Toggle({ enabled, setEnabled, label }: ToggleProps) {
  return (
    <div className="flex items-center space-x-4">
      {label && <span className="text-sm text-gray-700">{label}</span>}
      <Switch
        checked={enabled}
        onChange={setEnabled}
        className={`${
          enabled ? "bg-indigo-600" : "bg-gray-200"
        } relative inline-flex h-6 w-11 items-center rounded-full transition`}
      >
        <span
          className={`${
            enabled ? "translate-x-6" : "translate-x-1"
          } inline-block h-4 w-4 transform rounded-full bg-white transition`}
        />
      </Switch>
    </div>
  )
}
