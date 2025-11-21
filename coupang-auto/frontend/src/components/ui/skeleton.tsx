import { cn } from "../../lib/utils";

function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      className={cn(
        "bg-gray-800/50 animate-pulse rounded-md relative overflow-hidden",
        "before:absolute before:inset-0",
        "before:bg-gradient-to-r before:from-transparent before:via-cyan-500/10 before:to-transparent",
        "before:animate-shimmer",
        className
      )}
      {...props}
    />
  )
}

export { Skeleton }
