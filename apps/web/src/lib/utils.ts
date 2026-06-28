import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// shadcn/ui class-merge helper — repo is shadcn-ready; components added when first
// UI unit needs them (v1.0.8+) [C9a]. ponytail: util now, components on demand.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
