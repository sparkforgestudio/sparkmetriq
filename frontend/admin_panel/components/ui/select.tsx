import { SelectHTMLAttributes } from "react"
import clsx from "clsx"

type SelectProps = SelectHTMLAttributes<HTMLSelectElement>

export function Select({ className, ...props }: SelectProps) {
  return (
    <select
      {...props}
      className={clsx(
        "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
        className
      )}
    />
  )
}
