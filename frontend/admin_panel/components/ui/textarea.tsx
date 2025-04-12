import { TextareaHTMLAttributes } from "react"
import clsx from "clsx"

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>

export function Textarea({ className, ...props }: TextareaProps) {
  return (
    <textarea
      {...props}
      className={clsx(
        "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
        className
      )}
    />
  )
}
