# Klosado — we close.

AI client-acquisition machine for small marketing agencies. One productized loop:

```
LEAD → ENRICH → SCORE → OUTREACH → REPLY → NEGOTIATE → BOOK → DELIVER
```

Agencies white-label it under their brand. Our own cold outbound is the live demo.

## Repo layout

- `backend/` — FastAPI service: the Brain (model router + budgets), engines, API
- `docker-compose.yml` — Postgres + Redis + API (local dev / Coolify deploy)
- `.github/workflows/ci.yml` — lint + test on every push

## Quickstart (local)

```bash
cp backend/.env.example backend/.env   # fill in keys
docker compose up --build
curl localhost:8000/health
```

## Phases

- **Phase 0** (current): foundation — infra, repo, Brain v0
- **Phase 1**: dogfood MVP — the machine books our own first 5 demos
- **Phase 2**: first paying pilot agency
- **Phase 3**: productize — self-serve onboarding, billing
