import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium transition-all duration-300 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-blue-500/50",
  {
    variants: {
      variant: {
        default: "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-[1.02] active:scale-[0.98]",
        destructive:
          "bg-gradient-to-r from-red-500 to-rose-600 text-white shadow-lg shadow-red-500/25 hover:shadow-red-500/40 hover:scale-[1.02] active:scale-[0.98]",
        outline:
          "border border-white/10 bg-white/5 backdrop-blur-sm text-white/80 hover:bg-white/10 hover:text-white hover:border-white/20",
        secondary:
          "bg-white/10 backdrop-blur-sm text-white/80 hover:bg-white/15 hover:text-white",
        ghost:
          "text-white/60 hover:bg-white/5 hover:text-white",
        link: "text-blue-400 underline-offset-4 hover:underline hover:text-blue-300",
        glass: "glass-card text-white/80 hover:text-white hover:bg-white/10",
        glow: "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 animate-glow hover:scale-[1.02] active:scale-[0.98]",
      },
      size: {
        default: "h-10 px-5 py-2.5",
        sm: "h-8 rounded-lg gap-1.5 px-3 text-xs",
        lg: "h-12 rounded-xl px-8 text-base",
        icon: "size-10",
        "icon-sm": "size-8 rounded-lg",
        "icon-lg": "size-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
