import { useAccounts, useUpdateStatus } from "../hooks/useAccounts";
import styles from "./InvestigationQueue.module.css";

const TRANSITIONS: Record<string, string[]> = {
  flagged: ["reviewing", "dismissed"],
  reviewing: ["confirmed", "dismissed"],
  confirmed: [],
  dismissed: [],
};

function statusColorClass(status: string) {
  if (status === "confirmed") return styles.statusConfirmed;
  if (status === "reviewing") return styles.statusReviewing;
  if (status === "dismissed") return styles.statusDismissed;
  return styles.statusFlagged;
}

export function InvestigationQueue() {
  const { data: accounts = [], isLoading } = useAccounts(0.5, "flagged");
  const { data: reviewing = [] } = useAccounts(0, "reviewing");
  const { mutate: updateStatus } = useUpdateStatus();

  const queue = [...accounts, ...reviewing];

  if (isLoading) return <p className={styles.loading}>loading...</p>;

  return (
    <div className={styles.page}>
      <h2 className={styles.title}>Investigation Queue</h2>
      <p className={styles.subtitle}>
        {queue.length} account{queue.length !== 1 ? "s" : ""} need attention
      </p>

      <div className={styles.list}>
        {queue.length === 0 ? (
          <p className={styles.empty}>queue is clear</p>
        ) : (
          queue.map((account) => (
            <div key={account.id} className={styles.card}>
              <div className={styles.info}>
                <span className={styles.username}>{account.username}</span>
                <span className={styles.accountId}>{account.id}</span>
                <span className={`${styles.status} ${statusColorClass(account.status)}`}>
                  {account.status} · risk {account.risk_score.toFixed(2)}
                </span>
              </div>

              <div className={styles.actions}>
                {(TRANSITIONS[account.status] ?? []).map((next) => (
                  <button
                    key={next}
                    onClick={() => updateStatus({ accountId: account.id, status: next })}
                    className={`${styles.actionButton} ${next === "dismissed" ? styles.actionButtonDismiss : ""}`}
                  >
                    {next}
                  </button>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
