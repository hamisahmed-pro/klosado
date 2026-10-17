import os

import psycopg
from .config import settings


def _database_url() -> str:
    # Read live so tests (or orchestrators) can point at a DB via env at runtime.
    return os.environ.get("DATABASE_URL", settings.database_url)

DDL = """
CREATE TABLE IF NOT EXISTS client_budgets (
    client_id TEXT PRIMARY KEY,
    monthly_token_budget BIGINT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS usage_ledger (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    task_type TEXT NOT NULL,
    prompt_tokens INT NOT NULL,
    completion_tokens INT NOT NULL,
    cost_usd NUMERIC(12,6) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS usage_ledger_client_created
    ON usage_ledger (client_id, created_at);
"""


def get_conn():
    conn = psycopg.connect(_database_url())
    conn.execute(DDL)
    conn.commit()
    return conn
