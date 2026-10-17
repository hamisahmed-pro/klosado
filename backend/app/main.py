from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .brain import budgets, router
from .brain.budgets import BudgetExceeded

app = FastAPI(title="Klosado Brain", version="0.1.0")


class CompleteIn(BaseModel):
    client_id: str
    task_type: str = "volume"  # volume | smart | long_context | private
    prompt: str
    system: str = ""
    max_tokens: int = 1024
    temperature: float = 0.7


class BudgetIn(BaseModel):
    client_id: str
    monthly_token_budget: int


@app.get("/health")
def health():
    return {"ok": True, "service": "klosado-brain", "version": "0.1.0"}


@app.post("/v1/brain/complete")
def brain_complete(inp: CompleteIn):
    try:
        return router.complete(
            client_id=inp.client_id,
            task_type=inp.task_type,
            prompt=inp.prompt,
            system=inp.system,
            max_tokens=inp.max_tokens,
            temperature=inp.temperature,
        )
    except BudgetExceeded as e:
        raise HTTPException(status_code=402, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e))


@app.get("/v1/brain/usage/{client_id}")
def brain_usage(client_id: str):
    return {
        "client_id": client_id,
        "monthly_budget": budgets.get_budget(client_id),
        "month_used_tokens": budgets.month_usage(client_id),
    }


@app.post("/v1/brain/budget")
def brain_set_budget(inp: BudgetIn):
    budgets.set_budget(inp.client_id, inp.monthly_token_budget)
    return {"client_id": inp.client_id,
            "monthly_token_budget": inp.monthly_token_budget}
