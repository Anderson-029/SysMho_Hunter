-- ============================================================
-- SysMho Hunter - Funciones Almacenadas
-- ============================================================

-- Función: Crear o recuperar un target
CREATE OR REPLACE FUNCTION fn_upsert_target(
    p_hostname VARCHAR,
    p_base_url VARCHAR,
    p_ip_address VARCHAR DEFAULT NULL,
    p_scope JSONB DEFAULT '[]'::JSONB
)
RETURNS INTEGER AS $$
DECLARE
    v_target_id INTEGER;
BEGIN
    INSERT INTO targets (hostname, base_url, ip_address, scope)
    VALUES (p_hostname, p_base_url, p_ip_address, p_scope)
    ON CONFLICT (base_url) DO UPDATE
        SET ip_address = COALESCE(EXCLUDED.ip_address, targets.ip_address),
            scope = COALESCE(EXCLUDED.scope, targets.scope),
            updated_at = NOW()
    RETURNING id INTO v_target_id;

    RETURN v_target_id;
END;
$$ LANGUAGE plpgsql;


-- Función: Crear un nuevo escaneo
CREATE OR REPLACE FUNCTION fn_create_scan(
    p_scan_uid VARCHAR,
    p_target_id INTEGER,
    p_scan_type VARCHAR DEFAULT 'full',
    p_config JSONB DEFAULT '{}'::JSONB
)
RETURNS INTEGER AS $$
DECLARE
    v_scan_id INTEGER;
BEGIN
    INSERT INTO scans (scan_uid, target_id, scan_type, status, config)
    VALUES (p_scan_uid, p_target_id, p_scan_type, 'pending', p_config)
    RETURNING id INTO v_scan_id;

    -- Log inicial
    PERFORM fn_add_log(v_scan_id, 'info'::log_level,
        'Escaneo ' || p_scan_uid || ' creado. Tipo: ' || p_scan_type);

    RETURN v_scan_id;
END;
$$ LANGUAGE plpgsql;


-- Función: Actualizar estado de escaneo
CREATE OR REPLACE FUNCTION fn_update_scan_status(
    p_scan_id INTEGER,
    p_status scan_status,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE scans
    SET status = p_status,
        finished_at = CASE
            WHEN p_status IN ('completed', 'failed', 'cancelled')
            THEN NOW() ELSE finished_at
        END,
        duration_secs = CASE
            WHEN p_status IN ('completed', 'failed', 'cancelled')
            THEN EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER
            ELSE duration_secs
        END,
        error_message = COALESCE(p_error_message, error_message)
    WHERE id = p_scan_id;

    -- Log automático de cambio de estado
    PERFORM fn_add_log(p_scan_id, 'info'::log_level,
        'Estado actualizado a: ' || p_status::TEXT);
END;
$$ LANGUAGE plpgsql;


-- Función: Guardar datos de reconocimiento
CREATE OR REPLACE FUNCTION fn_save_recon_data(
    p_scan_id INTEGER,
    p_recon_data JSONB
)
RETURNS VOID AS $$
BEGIN
    UPDATE scans
    SET recon_data = p_recon_data
    WHERE id = p_scan_id;

    -- Actualizar tecnologías y headers del target
    UPDATE targets
    SET technologies = COALESCE(p_recon_data->'technologies', '[]'::JSONB),
        headers = COALESCE(p_recon_data->'headers', '{}'::JSONB),
        updated_at = NOW()
    WHERE id = (SELECT target_id FROM scans WHERE id = p_scan_id);
END;
$$ LANGUAGE plpgsql;


-- Función: Agregar un hallazgo
CREATE OR REPLACE FUNCTION fn_add_finding(
    p_scan_id INTEGER,
    p_finding_type VARCHAR,
    p_title VARCHAR,
    p_severity severity_level,
    p_description TEXT DEFAULT NULL,
    p_remediation TEXT DEFAULT NULL,
    p_evidence JSONB DEFAULT '{}'::JSONB,
    p_url_affected VARCHAR DEFAULT NULL,
    p_cvss_score DECIMAL DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_finding_id INTEGER;
    v_target_id INTEGER;
    v_is_dup BOOLEAN;
BEGIN
    -- Obtener target_id del escaneo
    SELECT target_id INTO v_target_id
    FROM scans WHERE id = p_scan_id;

    -- Verificar si es duplicado (mismo tipo + mismo target)
    SELECT EXISTS(
        SELECT 1 FROM findings
        WHERE target_id = v_target_id
          AND finding_type = p_finding_type
          AND title = p_title
          AND status != 'false_positive'
    ) INTO v_is_dup;

    INSERT INTO findings (
        scan_id, target_id, finding_type, title,
        severity, description, remediation, evidence,
        url_affected, cvss_score, is_duplicate
    ) VALUES (
        p_scan_id, v_target_id, p_finding_type, p_title,
        p_severity, p_description, p_remediation, p_evidence,
        p_url_affected, p_cvss_score, v_is_dup
    ) RETURNING id INTO v_finding_id;

    -- Log del hallazgo
    PERFORM fn_add_log(p_scan_id,
        CASE WHEN p_severity IN ('critical'::severity_level, 'high'::severity_level) THEN 'warning'::log_level ELSE 'info'::log_level END,
        '[' || p_severity::TEXT || '] ' || p_title
    );

    RETURN v_finding_id;
END;
$$ LANGUAGE plpgsql;


-- Función: Agregar log de escaneo
CREATE OR REPLACE FUNCTION fn_add_log(
    p_scan_id INTEGER,
    p_level log_level,
    p_message TEXT,
    p_metadata JSONB DEFAULT '{}'::JSONB
)
RETURNS INTEGER AS $$
DECLARE
    v_log_id INTEGER;
BEGIN
    INSERT INTO scan_logs (scan_id, level, message, metadata)
    VALUES (p_scan_id, p_level, p_message, p_metadata)
    RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;


-- Función: Obtener resumen del escaneo (para el dashboard)
CREATE OR REPLACE FUNCTION fn_get_scan_summary(p_scan_id INTEGER)
RETURNS TABLE (
    scan_uid VARCHAR,
    target_url VARCHAR,
    status scan_status,
    duration INTEGER,
    total_findings BIGINT,
    critical_count BIGINT,
    high_count BIGINT,
    medium_count BIGINT,
    low_count BIGINT,
    info_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.scan_uid,
        t.base_url,
        s.status,
        s.duration_secs,
        COUNT(f.id) AS total_findings,
        COUNT(f.id) FILTER (WHERE f.severity = 'critical') AS critical_count,
        COUNT(f.id) FILTER (WHERE f.severity = 'high') AS high_count,
        COUNT(f.id) FILTER (WHERE f.severity = 'medium') AS medium_count,
        COUNT(f.id) FILTER (WHERE f.severity = 'low') AS low_count,
        COUNT(f.id) FILTER (WHERE f.severity = 'info') AS info_count
    FROM scans s
    JOIN targets t ON s.target_id = t.id
    LEFT JOIN findings f ON f.scan_id = s.id
    WHERE s.id = p_scan_id
    GROUP BY s.scan_uid, t.base_url, s.status, s.duration_secs;
END;
$$ LANGUAGE plpgsql;


-- Función: Obtener los últimos N logs (para la terminal)
CREATE OR REPLACE FUNCTION fn_get_recent_logs(
    p_scan_id INTEGER,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    log_id INTEGER,
    level log_level,
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT sl.id, sl.level, sl.message, sl.metadata, sl.created_at
    FROM scan_logs sl
    WHERE sl.scan_id = p_scan_id
    ORDER BY sl.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


-- Función: Estadísticas globales (para el dashboard principal)
CREATE OR REPLACE FUNCTION fn_get_dashboard_stats()
RETURNS TABLE (
    total_scans BIGINT,
    active_scans BIGINT,
    total_findings BIGINT,
    critical_findings BIGINT,
    high_findings BIGINT,
    medium_findings BIGINT,
    low_findings BIGINT,
    total_targets BIGINT,
    total_reports BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM scans),
        (SELECT COUNT(*) FROM scans WHERE status IN ('recon', 'analyzing', 'reporting')),
        (SELECT COUNT(*) FROM findings WHERE NOT is_duplicate),
        (SELECT COUNT(*) FROM findings WHERE severity = 'critical' AND NOT is_duplicate),
        (SELECT COUNT(*) FROM findings WHERE severity = 'high' AND NOT is_duplicate),
        (SELECT COUNT(*) FROM findings WHERE severity = 'medium' AND NOT is_duplicate),
        (SELECT COUNT(*) FROM findings WHERE severity = 'low' AND NOT is_duplicate),
        (SELECT COUNT(*) FROM targets),
        (SELECT COUNT(*) FROM reports);
END;
$$ LANGUAGE plpgsql;


-- Función: Guardar reporte generado
CREATE OR REPLACE FUNCTION fn_save_report(
    p_scan_id INTEGER,
    p_title VARCHAR,
    p_content_md TEXT,
    p_platform VARCHAR DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_report_id INTEGER;
    v_target_id INTEGER;
BEGIN
    SELECT target_id INTO v_target_id
    FROM scans WHERE id = p_scan_id;

    INSERT INTO reports (scan_id, target_id, title, content_md, platform)
    VALUES (p_scan_id, v_target_id, p_title, p_content_md, p_platform)
    RETURNING id INTO v_report_id;

    PERFORM fn_add_log(p_scan_id, 'success'::log_level,
        'Reporte generado: ' || p_title);

    RETURN v_report_id;
END;
$$ LANGUAGE plpgsql;


-- Función: Limpiar logs antiguos (mantenimiento)
CREATE OR REPLACE FUNCTION fn_cleanup_old_logs(p_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM scan_logs
    WHERE created_at < NOW() - (p_days || ' days')::INTERVAL;
    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;
