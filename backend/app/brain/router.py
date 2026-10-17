"""The Brain: routes every AI task to the right model, enforcing per-client budgets.

Task types:
  volume       -> DeepSeek via hcnsec (cheap workhorse: scoring, drafting, classification)
  smart        -> DeepSeek-Pro via hcnsec (harder reasoning, negotiation)
  long_context -> Gemini (long documents, big lead lists)
  private      -> local Ollama/Qwen (anything that must not leave the box)
"""

from . import providers
from .budgets import BudgetExceeded, check_budget, record_usage

ROUTES = {
    "volume": ("hcnsec", providers.hcnsec_complete, {}),
    "smart": ("hcnsec", providers.hcnsec_complete,
              {"model": None}),  # resolved to smart model at call time
    "long_context": ("gemini", providers.gemini_complete, {}),
    "private": ("ollama", providers.ollama_complete, {}),
}

# Rough pre-call estimate so the budget gate can run before spending.
EST_TOKENS_PER_CALL = 4000


def complete(client_id: str, task_type: str, prompt: str,
             system: str = "", max_tokens: int = 1024,
             temperature: float = 0.7) -> dict:
    if task_type not in ROUTES:
        raise ValueError(f"unknown task_type '{task_type}' (want one of {sorted(ROUTES)})")
    provider_name, fn, extra = ROUTES[task_type]

    check_budget(client_id, EST_TOKENS_PER_CALL)

    kwargs = dict(extra)
    if task_type == "smart":
        from ..core.config import settings
        kwargs["model"] = settings.hcnsec_model_smart
    text, pt, ct, model = fn(prompt, system=system,
                             max_tokens=max_tokens, temperature=temperature,
                             **kwargs)
    cost = record_usage(client_id, provider_name, model, task_type, pt, ct)
    return {
        "text": text,
        "provider": provider_name,
        "model": model,
        "prompt_tokens": pt,
        "completion_tokens": ct,
        "cost_usd": round(cost, 6),
    }
