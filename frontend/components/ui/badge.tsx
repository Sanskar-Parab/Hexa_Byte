import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-ink text-white",
        secondary: "border-transparent bg-canvas-soft2 text-body",
        outline: "border-hairline text-ink bg-canvas",
        destructive: "border-transparent bg-err-soft text-err-deep",
        success: "border-transparent bg-link-soft text-link-deep",
        warning: "border-transparent bg-warn-soft text-warn-deep",
        info: "border-transparent bg-link-soft text-link-deep",
        violet: "border-transparent bg-violet-soft text-violet-deep",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
