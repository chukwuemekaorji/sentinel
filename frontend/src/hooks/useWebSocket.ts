import { useEffect, useRef, useState } from "react";
import type { Flag } from "./useAccounts";

export function useWebSocket() {
  const [liveFlags, setLiveFlags] = useState<Flag[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    function connect() {
      // connect to the websocket endpoint on the api
      const ws = new WebSocket("ws://localhost:8000/ws/flags");
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const flag = JSON.parse(event.data) as Flag;
          // prepend new flags so the newest always appears at the top
          setLiveFlags((prev) => [flag, ...prev].slice(0, 100));
        } catch {
          console.error("failed to parse websocket message", event.data);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        // try to reconnect after 3 seconds if the connection drops
        setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      wsRef.current?.close();
    };
  }, []);

  return { liveFlags, connected };
}