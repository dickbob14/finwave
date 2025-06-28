import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const fetcher = async (url: string) => {
  const res = await fetch(url, {
    headers: {
      'Authorization': 'Bearer demo-token', // Demo token for BYPASS_AUTH mode
      'Content-Type': 'application/json'
    }
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`Failed to fetch: ${res.status} ${error}`);
  }
  return res.json();
};