import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * useWebSocket - Hook para comunicación en tiempo real.
 * Implementa auto-reconexión y gestión de suscripciones.
 */
export const useWebSocket = (url) => {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log("WebSocket Connected ✅");
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      // Auto-reconnect after 3 seconds
      setTimeout(connect, 3000);
    };
    
    ws.onerror = () => setIsConnected(false);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessages(prev => [...prev.slice(-100), data]);
      } catch (e) {
        console.error("WS Parsing Error:", e);
      }
    };
  }, [url]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { messages, isConnected, send };
};
