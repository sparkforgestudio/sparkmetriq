import { LabelHTMLAttributes } from "react"
import clsx from "clsx"

type LabelProps = LabelHTMLAttributes<HTMLLabelElement>

export function Label({ className, ...props }: LabelProps) {
  return (
    <label
      {...props}
      className={clsx("block text-sm font-medium text-gray-700", className)}
    />
  )
}
