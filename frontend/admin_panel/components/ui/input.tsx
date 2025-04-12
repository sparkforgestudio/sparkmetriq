import { InputHTMLAttributes } from "react"
import clsx from "clsx"

type InputProps = InputHTMLAttributes<HTMLInputElement>

export function Input({ className, ...props }: InputProps) {
  return (
    <input
      {...props}
      className={clsx(
        "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
        className
      )}
    />
  )
}
