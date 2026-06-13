import { useQuery } from "@tanstack/react-query";
import type { Flag } from "./useAccounts";

async function fetchFlags(minScore = 0, source?: string): Promise<Flag[]> {
  const params = new URLSearchParams({ min_score: String(minScore) });
  if (source) params.append("source", source);

  const res = await fetch(`/api/flags/?${params}`);
  if (!res.ok) throw new Error("failed to fetch flags");
  return res.json();
}

export function useFlags(minScore = 0, source?: string) {
  return useQuery({
    queryKey: ["flags", minScore, source],
    queryFn: () => fetchFlags(minScore, source),
  });
}