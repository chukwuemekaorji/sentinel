import { useWebSocket } from "../hooks/useWebSocket";
import { useFlags } from "../hooks/useFlags";
import { FlagCard } from "../components/FlagCard";
import styles from "./LiveFeed.module.css";

export function LiveFeed() {
  const { liveFlags, connected } = useWebSocket();

  // load the initial batch of recent flags from the rest api
  // the websocket then appends new ones on top in real time
  const { data: initialFlags = [] } = useFlags(0.7);

  // merge live flags with initial ones, deduplicated by id
  const liveIds = new Set(liveFlags.map((f) => String(f.id)));
  const combined = [...liveFlags, ...initialFlags.filter((f) => !liveIds.has(String(f.id)))];

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h2 className={styles.title}>Live Feed</h2>
        <span className={`${styles.status} ${connected ? styles.statusConnected : ""}`}>
          <span className={`${styles.statusDot} ${connected ? styles.statusDotConnected : ""}`} />
          {connected ? "live" : "reconnecting..."}
        </span>
      </div>

      <div className={styles.list}>
        {combined.length === 0 ? (
          <p className={styles.empty}>waiting for high-risk flags...</p>
        ) : (
          combined.map((flag, i) => <FlagCard key={flag.id ?? i} flag={flag} />)
        )}
      </div>
    </div>
  );
}
