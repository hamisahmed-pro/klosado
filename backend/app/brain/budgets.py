"""Per-client monthly token budgets + append-only usage ledger."""

from ..core.config import settings
from ..core.db import get_conn

# Estimated USD per 1M tokens (blended in/out) for metering display.
COST_PER_MTOK = {
    "hcnsec": 0.15,
    "gemini": 0.50,
    "ollama": 0.0,
}


def get_budget(client_id: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT monthly_token_budget FROM client_budgets WHERE client_id=%s",
            (client_id,),
        ).fetchone()
        if row:
            return row[0]
        conn.execute(
            "INSERT INTO client_budgets (client_id, monthly_token_budget) VALUES (%s, %s)",
            (client_id, settings.default_monthly_token_budget),
        )
        conn.commit()
        return settings.default_monthly_token_budget


def set_budget(client_id: str, tokens: int) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO client_budgets (client_id, monthly_token_budget)
               VALUES (%s, %s)
               ON CONFLICT (client_id) DO UPDATE
               SET monthly_token_budget=EXCLUDED.monthly_token_budget, updated_at=now()""",
            (client_id, tokens),
        )
        conn.commit()


def month_usage(client_id: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT COALESCE(SUM(prompt_tokens + completion_tokens), 0)
               FROM usage_ledger
               WHERE client_id=%s
                 AND date_trunc('month', created_at) = date_trunc('month', now())""",
            (client_id,),
        ).fetchone()
        return row[0]


def check_budget(client_id: str, est_tokens: int) -> None:
    """Raise BudgetExceeded if this call would blow the monthly budget."""
    budget = get_budget(client_id)
    used = month_usage(client_id)
    if budget > 0 and used + est_tokens > budget:
        raise BudgetExceeded(client_id, budget, used)


def record_usage(client_id, provider, model, task_type,
                 prompt_tokens, completion_tokens) -> float:
    cost = (prompt_tokens + completion_tokens) / 1_000_000 * COST_PER_MTOK.get(provider, 0)
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO usage_ledger
               (client_id, provider, model, task_type, prompt_tokens, completion_tokens, cost_usd)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (client_id, provider, model, task_type,
             prompt_tokens, completion_tokens, cost),
        )
        conn.commit()
    return cost


class BudgetExceeded(Exception):
    def __init__(self, client_id, budget, used):
        super().__init__(
            f"client '{client_id}' exceeded monthly token budget "
            f"({used:,}/{budget:,} used)"
        )
        self.client_id = client_id
        self.budget = budget
        self.used = used
