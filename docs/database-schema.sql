-- Esquema mínimo requerido por el bot en la base PostgreSQL compartida

CREATE TABLE IF NOT EXISTS ledger_entries (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    ts BIGINT NOT NULL,
    date_iso VARCHAR(32) NOT NULL,
    amount BIGINT NOT NULL,
    currency VARCHAR(12) NOT NULL,
    category VARCHAR(128) NOT NULL,
    description TEXT DEFAULT '',
    payee VARCHAR(255) DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ledger_chat_message UNIQUE (chat_id, message_id)
);

CREATE TABLE IF NOT EXISTS bot_state (
    key VARCHAR(64) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
