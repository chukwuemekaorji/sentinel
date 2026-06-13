import styles from "./Sidebar.module.css";

interface Props {
  activeView: string;
  onNavigate: (view: string) => void;
}

const views = [
  { id: "live", label: "Live Feed" },
  { id: "accounts", label: "Flagged Accounts" },
  { id: "graph", label: "Graph View" },
  { id: "queue", label: "Investigation Queue" },
];

export function Sidebar({ activeView, onNavigate }: Props) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          SENTINEL
        </h1>
        <p className={styles.subtitle}>
          anomaly detection
        </p>
      </div>

      {views.map((view) => (
        <button
          key={view.id}
          onClick={() => onNavigate(view.id)}
          className={`${styles.navButton} ${activeView === view.id ? styles.navButtonActive : ""}`}
        >
          {view.label}
        </button>
      ))}
    </aside>
  );
}
