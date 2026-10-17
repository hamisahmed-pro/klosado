"""Model providers. Each exposes: complete(prompt, system, max_tokens, temperature)
-> (text, prompt_tokens, completion_tokens). Token counts are best-effort
estimates when the provider does not report them."""

import json
import sys
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request  # noqa: E402

from ..core.config import settings  # noqa: E402

HCNSEC_BASE = "https://api.hcnsec.cn/v1"
HCNSEC_CRED = "custom.hcnsec"


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def hcnsec_complete(prompt, system="", max_tokens=1024, temperature=0.7, model=None):
    model = model or settings.hcnsec_model_volume
    payload = {
        "model": model,
        "messages": ([{"role": "system", "content": system}] if system else [])
        + [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    req = urllib.request.Request(
        HCNSEC_BASE + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    add_surrogate_to_request(req, HCNSEC_CRED, entry_name="access_token",
                             allowed_hosts=["api.hcnsec.cn"])
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.load(resp)
    msg = body["choices"][0]["message"]["content"]
    usage = body.get("usage", {})
    pt = usage.get("prompt_tokens") or _estimate_tokens((system or "") + prompt)
    ct = usage.get("completion_tokens") or _estimate_tokens(msg)
    return msg, pt, ct, model


def gemini_complete(prompt, system="", max_tokens=1024, temperature=0.7):
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")
    import httpx

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}")
    parts = ([{"text": system}] if system else []) + [{"text": prompt}]
    r = httpx.post(url, json={
        "contents": [{"parts": parts}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
    }, timeout=120)
    r.raise_for_status()
    body = r.json()
    text = body["candidates"][0]["content"]["parts"][0]["text"]
    meta = body.get("usageMetadata", {})
    pt = meta.get("promptTokenCount") or _estimate_tokens((system or "") + prompt)
    ct = meta.get("candidatesTokenCount") or _estimate_tokens(text)
    return text, pt, ct, settings.gemini_model


def ollama_complete(prompt, system="", max_tokens=1024, temperature=0.7):
    import httpx

    r = httpx.post(f"{settings.ollama_base_url}/api/generate", json={
        "model": settings.ollama_model,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature},
    }, timeout=300)
    r.raise_for_status()
    body = r.json()
    text = body["response"]
    pt = body.get("prompt_eval_count") or _estimate_tokens((system or "") + prompt)
    ct = body.get("eval_count") or _estimate_tokens(text)
    return text, pt, ct, settings.ollama_model
