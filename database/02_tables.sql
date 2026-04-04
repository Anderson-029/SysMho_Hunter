-- ============================================================
-- SysMho Hunter - Tablas e Índices
-- ============================================================

-- Targets: dominios/IPs que se analizan
CREATE TABLE IF NOT EXISTS targets (
    id              SERIAL PRIMARY KEY,
    hostname        VARCHAR(512) NOT NULL,
    base_url        VARCHAR(1024) NOT NULL,
    ip_address      VARCHAR(45),
    scope           JSONB DEFAULT '[]'::JSONB,
    technologies    JSONB DEFAULT '[]'::JSONB,
    headers         JSONB DEFAULT '{}'::JSONB,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(base_url)
);

-- Escaneos: sesiones de escaneo
CREATE TABLE IF NOT EXISTS scans (
    id              SERIAL PRIMARY KEY,
    scan_uid        VARCHAR(16) NOT NULL UNIQUE,
    target_id       INTEGER REFERENCES targets(id) ON DELETE CASCADE,
    scan_type       VARCHAR(20) NOT NULL DEFAULT 'full',
    status          scan_status NOT NULL DEFAULT 'pending',
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    duration_secs   INTEGER,
    recon_data      JSONB DEFAULT '{}'::JSONB,
    config          JSONB DEFAULT '{}'::JSONB,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Hallazgos (vulnerabilidades encontradas)
CREATE TABLE IF NOT EXISTS findings (
    id              SERIAL PRIMARY KEY,
    scan_id         INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    target_id       INTEGER REFERENCES targets(id) ON DELETE CASCADE,
    finding_type    VARCHAR(100) NOT NULL,
    title           VARCHAR(512) NOT NULL,
    severity        severity_level NOT NULL DEFAULT 'info',
    description     TEXT,
    remediation     TEXT,
    evidence        JSONB DEFAULT '{}'::JSONB,
    url_affected    VARCHAR(2048),
    status          finding_status NOT NULL DEFAULT 'new',
    cvss_score      DECIMAL(3,1),
    is_duplicate    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla para pensamientos tácticos de la IA
CREATE TABLE IF NOT EXISTS agent_thoughts (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    thought TEXT NOT NULL,
    proposed_action TEXT,
    priority VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Acciones pendientes de aprobación humana
CREATE TABLE IF NOT EXISTS pending_actions (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    command TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    reason_thought TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Logs de escaneo (para la terminal en tiempo real)
CREATE TABLE IF NOT EXISTS scan_logs (
    id              SERIAL PRIMARY KEY,
    scan_id         INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    level           log_level NOT NULL DEFAULT 'info',
    message         TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}'::JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Reportes generados
CREATE TABLE IF NOT EXISTS reports (
    id              SERIAL PRIMARY KEY,
    scan_id         INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    target_id       INTEGER REFERENCES targets(id) ON DELETE CASCADE,
    title           VARCHAR(512),
    content_md      TEXT NOT NULL,
    format          VARCHAR(20) DEFAULT 'markdown',
    platform        VARCHAR(50),
    submitted       BOOLEAN DEFAULT FALSE,
    submitted_at    TIMESTAMPTZ,
    bounty_amount   DECIMAL(10,2),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Payloads personalizados
CREATE TABLE IF NOT EXISTS custom_payloads (
    id              SERIAL PRIMARY KEY,
    category        VARCHAR(100) NOT NULL,
    payload         TEXT NOT NULL,
    description     VARCHAR(512),
    success_count   INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category, payload)
);

-- Configuración general del agente
CREATE TABLE IF NOT EXISTS agent_config (
    key             VARCHAR(100) PRIMARY KEY,
    value           TEXT NOT NULL,
    description     VARCHAR(512),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES PARA RENDIMIENTO
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status);
CREATE INDEX IF NOT EXISTS idx_scans_target ON scans(target_id);
CREATE INDEX IF NOT EXISTS idx_scans_uid ON scans(scan_uid);
CREATE INDEX IF NOT EXISTS idx_findings_scan ON findings(scan_id);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status);
CREATE INDEX IF NOT EXISTS idx_scan_logs_scan ON scan_logs(scan_id);
CREATE INDEX IF NOT EXISTS idx_scan_logs_created ON scan_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_reports_scan ON reports(scan_id);
