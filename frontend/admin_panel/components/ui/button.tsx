import { ButtonHTMLAttributes } from "react"
import clsx from "clsx"

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger"
}

export function Button({ variant = "primary", className, ...props }: ButtonProps) {
  const base =
    "px-4 py-2 rounded font-semibold text-sm transition duration-200 focus:outline-none"

  const variants = {
    primary: "bg-indigo-600 text-white hover:bg-indigo-700",
    secondary: "bg-gray-100 text-gray-800 hover:bg-gray-200",
    danger: "bg-red-500 text-white hover:bg-red-600",
  }

  return (
    <button
      {...props}
      className={clsx(base, variants[variant], className)}
    />
  )
}
