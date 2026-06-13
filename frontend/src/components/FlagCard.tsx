import type { Flag } from "../hooks/useAccounts";
import styles from "./FlagCard.module.css";

interface Props {
  flag: Flag;
}

// colour the score badge based on how serious the flag is
function scoreColorClass(score: number) {
  if (score >= 0.8) return styles.scoreHigh;  // red — high risk
  if (score >= 0.5) return styles.scoreMedium; // amber — medium
  return styles.scoreLow;                      // green — low
}

// human readable label for which detection layer caught this
function sourceLabel(source: string) {
  if (source === "rule_engine") return "Rule";
  if (source === "graph_analyzer") return "Graph";
  if (source === "anomaly_detector") return "Anomaly";
  return source;
}

export function FlagCard({ flag }: Props) {
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.accountId}>{flag.account_id}</span>
        <span className={`${styles.scoreBadge} ${scoreColorClass(flag.score)}`}>
          {flag.score.toFixed(2)}
        </span>
      </div>

      <div className={styles.meta}>
        <span className={styles.sourceBadge}>
          {sourceLabel(flag.source)}
        </span>
        <span className={styles.timestamp}>
          {new Date(flag.created_at).toLocaleTimeString()}
        </span>
      </div>

      <p className={styles.reason}>
        {flag.reason}
      </p>
    </div>
  );
}
