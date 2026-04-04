-- ============================================================
-- SysMho Hunter - Tipos de Datos (ENUMs)
-- ============================================================

DO $$ BEGIN
    CREATE TYPE scan_status AS ENUM (
        'pending', 'recon', 'analyzing',
        'reporting', 'completed', 'failed', 'cancelled'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE severity_level AS ENUM (
        'info', 'low', 'medium', 'high', 'critical'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE log_level AS ENUM (
        'debug', 'info', 'success', 'warning', 'error'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE finding_status AS ENUM (
        'new', 'confirmed', 'false_positive',
        'reported', 'fixed'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
