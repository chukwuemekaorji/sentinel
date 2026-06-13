import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { LiveFeed } from "./views/LiveFeed";
import { AccountsTable } from "./views/AccountsTable";
import { GraphView } from "./views/GraphView";
import { InvestigationQueue } from "./views/InvestigationQueue";
import styles from "./App.module.css";

type View = "live" | "accounts" | "graph" | "queue";

export default function App() {
  const [activeView, setActiveView] = useState<View>("live");

  function renderView() {
    if (activeView === "live") return <LiveFeed />;
    if (activeView === "accounts") return <AccountsTable />;
    if (activeView === "graph") return <GraphView />;
    if (activeView === "queue") return <InvestigationQueue />;
    return null;
  }

  return (
    <div className={styles.app}>
      <Sidebar activeView={activeView} onNavigate={(v) => setActiveView(v as View)} />
      <main className={styles.main}>
        {renderView()}
      </main>
    </div>
  );
}