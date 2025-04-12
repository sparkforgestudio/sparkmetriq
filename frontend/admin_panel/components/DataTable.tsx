"use client"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export function DataTable({ headers, data }: { headers: string[]; data: any[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full table-auto border-collapse mt-4">
        <thead className="bg-gray-100 text-left">
          <tr>
            {headers.map((header) => (
              <th key={header} className="px-4 py-2 text-sm font-semibold uppercase">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx} className="border-t">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-2 text-sm">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
