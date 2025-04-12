import { ReactNode } from "react"

type StatCardProps = {
  title: string
  value: string | number
  icon?: ReactNode
  className?: string
}

export default function StatCard({ title, value, icon, className }: StatCardProps) {
  return (
    <div className={`bg-white p-4 rounded-xl shadow border border-gray-200 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm text-gray-500">{title}</h4>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        {icon && <div className="text-4xl text-indigo-500">{icon}</div>}
      </div>
    </div>
  )
}
