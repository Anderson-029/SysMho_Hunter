-- ============================================================
-- SysMho Hunter - Datos Iniciales y Configuración
-- ============================================================

INSERT INTO agent_config (key, value, description) VALUES
    ('max_concurrent_scans', '3', 'Máximo de escaneos simultáneos'),
    ('default_rate_limit', '10', 'Peticiones por segundo por defecto'),
    ('scan_timeout', '300', 'Timeout de escaneo en segundos'),
    ('auto_report', 'true', 'Generar reporte automáticamente al terminar'),
    ('default_scan_type', 'full', 'Tipo de escaneo por defecto'),
    ('wordlist_path', '/usr/share/wordlists/dirb/common.txt', 'Ruta del wordlist para fuzzing')
ON CONFLICT (key) DO NOTHING;
