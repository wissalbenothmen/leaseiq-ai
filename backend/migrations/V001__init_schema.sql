-- LeaseIQ AI - Initial Schema
-- PostgreSQL 15+

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── Users ────────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(50)  NOT NULL DEFAULT 'tenant',
    is_active       VARCHAR(5)   NOT NULL DEFAULT 'true',
    company_id      UUID,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_users_email      ON users (email);
CREATE INDEX ix_users_company_id ON users (company_id);

-- ─── Commercial Leases ────────────────────────────────────────────────────────
CREATE TABLE commercial_leases (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_address    VARCHAR(500) NOT NULL,
    tenant_name         VARCHAR(255) NOT NULL,
    landlord_name       VARCHAR(255) NOT NULL,
    lease_type          VARCHAR(50)  NOT NULL DEFAULT 'gross',
    -- gross | net | nnn | modified_gross
    term_start          DATE         NOT NULL,
    term_end            DATE         NOT NULL,
    base_rent           NUMERIC(15, 2),
    rent_escalation_pct NUMERIC(5, 2),
    status              VARCHAR(50)  NOT NULL DEFAULT 'active',
    -- active | expired | terminated | pending | renewal
    suite_number        VARCHAR(100),
    square_footage      NUMERIC(10, 2),
    notes               TEXT,
    created_by          UUID,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_commercial_leases_tenant_name   ON commercial_leases (tenant_name);
CREATE INDEX ix_commercial_leases_landlord_name ON commercial_leases (landlord_name);
CREATE INDEX ix_commercial_leases_term_end      ON commercial_leases (term_end);
CREATE INDEX ix_commercial_leases_status        ON commercial_leases (status);
CREATE INDEX idx_tenant_landlord                ON commercial_leases (tenant_name, landlord_name);
CREATE INDEX idx_term_dates                     ON commercial_leases (term_start, term_end);

-- ─── Lease Clauses ────────────────────────────────────────────────────────────
CREATE TABLE lease_clauses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id            UUID NOT NULL REFERENCES commercial_leases (id),
    clause_type         VARCHAR(100) NOT NULL,
    extracted_text      TEXT         NOT NULL,
    risk_score          INTEGER      NOT NULL DEFAULT 0,
    risk_factors        JSONB,
    landlord_favorable  VARCHAR(5)   NOT NULL DEFAULT 'false',
    tenant_favorable    VARCHAR(5)   NOT NULL DEFAULT 'false',
    confidence_score    DOUBLE PRECISION,
    extraction_json     JSONB,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_lease_clauses_lease_id    ON lease_clauses (lease_id);
CREATE INDEX ix_lease_clauses_clause_type ON lease_clauses (clause_type);

-- ─── Lease Documents ──────────────────────────────────────────────────────────
CREATE TABLE lease_documents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id            UUID NOT NULL REFERENCES commercial_leases (id),
    filename            VARCHAR(500) NOT NULL,
    blob_url            VARCHAR(1000),
    ocr_text            TEXT,
    extraction_status   VARCHAR(50)  NOT NULL DEFAULT 'pending',
    -- pending | in_progress | complete | failed
    confidence_score    DOUBLE PRECISION,
    page_count          INTEGER,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_lease_documents_lease_id ON lease_documents (lease_id);

-- ─── Critical Dates ───────────────────────────────────────────────────────────
CREATE TABLE critical_dates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id        UUID NOT NULL REFERENCES commercial_leases (id),
    date_type       VARCHAR(100) NOT NULL,
    -- lease_expiry | renewal_option | rent_escalation | option_exercise | cam_reconciliation
    date_value      DATE         NOT NULL,
    days_until      INTEGER,
    alert_sent      VARCHAR(5)   NOT NULL DEFAULT 'false',
    alert_sent_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_critical_dates_lease_id  ON critical_dates (lease_id);
CREATE INDEX ix_critical_dates_type      ON critical_dates (date_type);
CREATE INDEX ix_critical_dates_value     ON critical_dates (date_value);
CREATE INDEX idx_lease_date_type         ON critical_dates (lease_id, date_type);

-- ─── Obligations ──────────────────────────────────────────────────────────────
CREATE TABLE obligations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id            UUID NOT NULL REFERENCES commercial_leases (id),
    obligation_type     VARCHAR(100) NOT NULL,
    -- rent | cam | insurance | maintenance | tax | reporting | inspection | other
    due_date            DATE         NOT NULL,
    recurrence          VARCHAR(50)  NOT NULL DEFAULT 'one_time',
    -- one_time | monthly | quarterly | annually
    status              VARCHAR(50)  NOT NULL DEFAULT 'pending',
    -- pending | completed | overdue | waived
    amount              NUMERIC(15, 2),
    description         VARCHAR(1000),
    responsible_party   VARCHAR(255),
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_obligations_lease_id        ON obligations (lease_id);
CREATE INDEX ix_obligations_type            ON obligations (obligation_type);
CREATE INDEX ix_obligations_due_date        ON obligations (due_date);
CREATE INDEX ix_obligations_status         ON obligations (status);
CREATE INDEX idx_lease_due_date             ON obligations (lease_id, due_date);
CREATE INDEX idx_status_due_date            ON obligations (status, due_date);

-- ─── Audit Logs ───────────────────────────────────────────────────────────────
CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id    UUID REFERENCES commercial_leases (id),
    user_id     UUID REFERENCES users (id),
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id   VARCHAR(255),
    changes     JSONB,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_audit_logs_lease_id   ON audit_logs (lease_id);
CREATE INDEX ix_audit_logs_action     ON audit_logs (action);
CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);

-- ─── Updated_at triggers ──────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_commercial_leases_updated_at
    BEFORE UPDATE ON commercial_leases
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_lease_clauses_updated_at
    BEFORE UPDATE ON lease_clauses
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_lease_documents_updated_at
    BEFORE UPDATE ON lease_documents
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_critical_dates_updated_at
    BEFORE UPDATE ON critical_dates
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_obligations_updated_at
    BEFORE UPDATE ON obligations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
