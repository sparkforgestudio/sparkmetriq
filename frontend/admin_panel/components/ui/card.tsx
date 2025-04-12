"use client"

import { ReactNode } from "react"

export function Card({ children }: { children: ReactNode }) {
  return (
    <div className="bg-white shadow rounded-xl p-4 border border-gray-200">
      {children}
    </div>
  )
}
