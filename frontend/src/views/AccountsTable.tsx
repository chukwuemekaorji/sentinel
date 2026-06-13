import { useState } from "react";
import { useAccounts, useUpdateStatus } from "../hooks/useAccounts";
import styles from "./AccountsTable.module.css";

const STATUS_OPTIONS = ["flagged", "reviewing", "confirmed", "dismissed"];

function riskColorClass(score: number) {
  if (score >= 0.8) return styles.riskHigh;
  if (score >= 0.5) return styles.riskMedium;
  return styles.riskLow;
}

export function AccountsTable() {
  const [minRisk, setMinRisk] = useState(0);
  const { data: accounts = [], isLoading } = useAccounts(minRisk);
  const { mutate: updateStatus } = useUpdateStatus();

  if (isLoading) return <p className={styles.loading}>loading...</p>;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h2 className={styles.title}>Flagged Accounts</h2>
        <div className={styles.filter}>
          <label htmlFor="min-risk" className={styles.filterLabel}>min risk</label>
          <input
            id="min-risk"
            type="range"
            min={0}
            max={1}
            step={0.1}
            value={minRisk}
            onChange={(e) => setMinRisk(Number(e.target.value))}
            className={styles.filterSlider}
          />
          <span className={styles.filterValue}>{minRisk.toFixed(1)}</span>
        </div>
      </div>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr className={styles.headerRow}>
              {["Account", "Username", "Followers", "Following", "Risk Score", "Status", "Action"].map((h) => (
                <th key={h} className={styles.headerCell}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {accounts.map((account) => (
              <tr key={account.id} className={styles.row}>
                <td className={styles.cellMuted}>
                  {account.id}
                </td>
                <td className={styles.cellBold}>
                  {account.username}
                </td>
                <td className={styles.cell}>{account.follower_count.toLocaleString()}</td>
                <td className={styles.cell}>{account.following_count.toLocaleString()}</td>
                <td className={styles.cell}>
                  <span className={`${styles.riskScore} ${riskColorClass(account.risk_score)}`}>
                    {account.risk_score.toFixed(2)}
                  </span>
                </td>
                <td className={styles.cell}>
                  <span className={styles.statusBadge}>
                    {account.status}
                  </span>
                </td>
                <td className={styles.cell}>
                  <select
                    aria-label={`status for ${account.username}`}
                    value={account.status}
                    onChange={(e) => updateStatus({ accountId: account.id, status: e.target.value })}
                    className={styles.statusSelect}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {accounts.length === 0 && (
          <p className={styles.empty}>
            no accounts match the current filter
          </p>
        )}
      </div>
    </div>
  );
}
