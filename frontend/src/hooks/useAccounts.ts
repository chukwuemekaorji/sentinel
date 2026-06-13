import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export interface Account {
  id: string;
  username: string;
  follower_count: number;
  following_count: number;
  post_count: number;
  risk_score: number;
  status: string;
  created_at: string;
}

export interface Flag {
  id: number;
  account_id: string;
  source: string;
  reason: string;
  score: number;
  created_at: string;
}

async function fetchAccounts(minRisk = 0, status?: string): Promise<Account[]> {
  const params = new URLSearchParams({ min_risk: String(minRisk) });
  if (status) params.append("status", status);

  const res = await fetch(`/api/accounts?${params}`);
  if (!res.ok) throw new Error("failed to fetch accounts");
  return res.json();
}

async function fetchAccountFlags(accountId: string): Promise<Flag[]> {
  const res = await fetch(`/api/accounts/${accountId}/flags`);
  if (!res.ok) throw new Error("failed to fetch flags");
  return res.json();
}

async function updateAccountStatus(accountId: string, status: string) {
  const res = await fetch(`/api/accounts/${accountId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error("failed to update status");
  return res.json();
}

export function useAccounts(minRisk = 0, status?: string) {
  return useQuery({
    queryKey: ["accounts", minRisk, status],
    queryFn: () => fetchAccounts(minRisk, status),
  });
}

export function useAccountFlags(accountId: string) {
  return useQuery({
    queryKey: ["account-flags", accountId],
    queryFn: () => fetchAccountFlags(accountId),
    enabled: !!accountId,
  });
}

export function useUpdateStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ accountId, status }: { accountId: string; status: string }) =>
      updateAccountStatus(accountId, status),
    onSuccess: () => {
      // refetch accounts after a status update so the table stays in sync
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });
}