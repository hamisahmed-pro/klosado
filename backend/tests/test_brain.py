"""Brain v0 tests: routing validation + budget enforcement (no real provider calls)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.brain import budgets, router

client = TestClient(app)


@pytest.fixture()
def tiny_budget():
    budgets.set_budget("test-client", 100)  # 100 tokens/mo
    yield "test-client"
    budgets.set_budget("test-client", 2_000_000)


def test_health():
    assert client.get("/health").json()["ok"] is True


def test_unknown_task_type_rejected():
    r = client.post("/v1/brain/complete", json={
        "client_id": "test-client", "task_type": "teleport", "prompt": "hi"})
    assert r.status_code == 400


def test_budget_exceeded_returns_402(tiny_budget):
    # Pre-call estimate (4000) already exceeds the 100-token budget.
    r = client.post("/v1/brain/complete", json={
        "client_id": tiny_budget, "task_type": "volume", "prompt": "hi"})
    assert r.status_code == 402
    assert "budget" in r.json()["detail"].lower()


def test_usage_endpoint_reports_numbers():
    budgets.set_budget("usage-client", 5000)
    r = client.get("/v1/brain/usage/usage-client").json()
    assert r["monthly_budget"] == 5000
    assert r["month_used_tokens"] >= 0


def test_set_budget_roundtrip():
    r = client.post("/v1/brain/budget", json={
        "client_id": "rt-client", "monthly_token_budget": 12345}).json()
    assert r["monthly_token_budget"] == 12345
    assert budgets.get_budget("rt-client") == 12345


def test_record_usage_meters_cost():
    cost = budgets.record_usage("meter-client", "hcnsec", "DeepSeek-V4.1-Flash",
                                "volume", 1_000_000, 1_000_000)
    assert cost == pytest.approx(0.30)  # 2M tokens @ $0.15/MTok


def test_router_rejects_before_spend(monkeypatch, tiny_budget):
    """Budget gate must fire before any provider is touched."""
    called = []

    def fake_provider(*a, **k):
        called.append(True)
        return "x", 1, 1, "m"

    monkeypatch.setitem(router.ROUTES, "volume", ("hcnsec", fake_provider, {}))
    with pytest.raises(budgets.BudgetExceeded):
        router.complete(tiny_budget, "volume", "hi")
    assert called == []
