import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "h-11 w-full min-w-0 rounded-xl px-4 py-2.5 text-sm",
        "glass-input text-white placeholder:text-white/30",
        "transition-all duration-300 outline-none",
        "focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50",
        "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
        "file:text-white file:bg-white/10 file:border-0 file:rounded-lg file:px-3 file:py-1 file:text-sm file:font-medium file:mr-3",
        className
      )}
      {...props}
    />
  )
}

export { Input }
