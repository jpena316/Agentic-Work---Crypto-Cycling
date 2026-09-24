import type { HTMLAttributes } from "react";
import { Card as BaseCard } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <BaseCard className={cn("p-5", className)} {...props} />;
}
