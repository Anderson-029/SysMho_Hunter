import { useState, useCallback } from 'react';

/**
 * useScanner - Hook para gestionar el ciclo de vida de los escaneos.
 * Centraliza el inicio, polling de estado y obtención de hallazgos.
 */
export const useScanner = (apiUrl = 'http://127.0.0.1:8000/api/v1') => {
  const [isScanning, setIsScanning] = useState(false);
  const [scanStatus, setScanStatus] = useState(null);
  const [findings, setFindings] = useState([]);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  const startScan = useCallback(async (targetUrl, scanType = 'full') => {
    if (!targetUrl?.trim()) return null;
    
    setIsScanning(true);
    setError(null);
    setLogs([]);
    setFindings([]);
    setScanStatus({ status: 'recon' });

    try {
      const response = await fetch(`${apiUrl}/scan/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_url: targetUrl, scan_type: scanType }),
      });
      
      if (!response.ok) throw new Error('Falla al iniciar escaneo');
      
      const data = await response.json();
      const scanUid = data.scan_id;

      // Iniciar Polling
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`${apiUrl}/scan/${scanUid}/status`);
          const statusData = await statusRes.json();
          
          setScanStatus(statusData);
          if (statusData.logs) setLogs(statusData.logs);

          if (statusData.status === 'completed' || statusData.status === 'failed') {
            clearInterval(pollInterval);
            setIsScanning(false);

            if (statusData.status === 'completed') {
              const findingsRes = await fetch(`${apiUrl}/scan/${scanUid}/findings`);
              const findingsData = await findingsRes.json();
              setFindings(findingsData.findings || []);
            }
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 2000);

      return scanUid;
    } catch (err) {
      setError(err.message);
      setIsScanning(false);
      return null;
    }
  }, [apiUrl]);

  return {
    isScanning,
    scanStatus,
    findings,
    logs,
    error,
    startScan,
    setLogs
  };
};
