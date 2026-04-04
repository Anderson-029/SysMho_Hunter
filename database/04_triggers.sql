-- ============================================================
-- SysMho Hunter - Triggers y Automatismos
-- ============================================================

-- Función de soporte para triggers de actualización de fecha
CREATE OR REPLACE FUNCTION trg_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-actualizar updated_at en targets
DROP TRIGGER IF EXISTS trg_targets_updated ON targets;
CREATE TRIGGER trg_targets_updated
    BEFORE UPDATE ON targets
    FOR EACH ROW
    EXECUTE FUNCTION trg_update_timestamp();
