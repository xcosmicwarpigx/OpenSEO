# AGENTS.md — OpenSEO Contributor Guide

This file is the practical playbook for people (and coding agents) contributing to OpenSEO.

## Project Purpose

OpenSEO is an open-source SEO analysis platform with:
- **Technical crawling** (Playwright + async tasks)
- **Competitive intelligence** (keyword gap, share-of-voice, overview)
- **Content optimizer**
- **Bulk URL analyzer**
- **One-shot full audit**

Default posture is **local-first**: compute on-device and avoid paid third-party SEO APIs unless explicitly added.

## Architecture (high level)

- `backend/` — FastAPI API, Celery tasks, analysis utilities
  - `main.py` = route definitions + endpoint catalog
  - `tasks/` = async/background workloads (`crawler.py`, `competitive.py`)
  - `tools/` = direct analyzers (`full_audit.py`, content/bulk tools)
  - `models.py` = shared request/response models + normalization
- `frontend/` — React + TypeScript + Vite
  - `src/api.ts` = **single source of truth** for frontend endpoints
  - `src/pages/*` = feature pages
- `redis` — broker/result backend for Celery
- `docker-compose.yml` — local multi-service orchestration

## Setup / Run / Test

### Docker (recommended)
```bash
cp .env.example .env
# optional: set GOOGLE_PAGESPEED_API_KEY in .env
make up-build
# or: docker-compose up --build -d
```

Services:
- Frontend: `http://localhost:5173`
- Backend/API docs: `http://localhost:8000` / `http://localhost:8000/docs`

Stop:
```bash
make down
```

### Local dev (without Docker)
Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
playwright install chromium
uvicorn main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

### Tests
Backend:
```bash
cd backend
pytest
pytest tests/unit -v
pytest tests/integration -v
pytest --cov
```

Frontend:
```bash
cd frontend
npm test
npm run coverage
```

## Coding Standards

### Python (backend)
- Follow PEP 8
- Format with `black .`
- Sort imports with `isort .`
- Keep route contracts explicit via Pydantic models
- Prefer pure utility functions in `utils/` for analyzers

### TypeScript/React (frontend)
- Keep TypeScript strict; avoid `any` unless justified
- Keep API calls in `src/api.ts` (not scattered across components)
- Use small, composable components and typed request payloads

## Deterministic Endpoint Policy (important)

When writing tests, automations, or reproducible integrations:

1. **Prefer deterministic endpoints** under `/api/deterministic/*` when available.
   - They block until completion (or timeout) and return final payload.
2. Use async start/status polling endpoints only for user-facing progress UX.
3. Keep deterministic behavior bounded with explicit `timeout_seconds`.
4. If adding a feature with async Celery routes, add a deterministic sibling when feasible.
5. Keep endpoint metadata in backend `ENDPOINT_CATALOG` (`/api/catalog`) current.

## Local-First Philosophy

- Default to local extraction/analysis and on-device computation.
- External APIs must be optional, gated by config/env, and never required for core paths.
- Avoid introducing vendor lock-in for baseline capabilities.
- Preserve graceful behavior when optional API keys are missing.

## Frontend Endpoint Map Rule (strict)

`frontend/src/api.ts` is the **single endpoint map**.

When adding/changing backend routes:
1. Update backend routes and `/api/catalog` (`ENDPOINT_CATALOG`).
2. Update `ENDPOINTS` and `apiClient` in `frontend/src/api.ts`.
3. Update/add tests that touch those endpoints.
4. Do **not** hardcode `/api/...` paths directly in page/component files.

## Docker + Tunnel Notes

- Frontend uses same-origin by default (`VITE_API_URL` defaults to empty), preventing localhost leakage when served via public/tunnel hostnames.
- Vite dev server proxies `/api` to `http://backend:8000` in Docker network.
- `allowedHosts: true` in Vite config supports Cloudflare tunnel/custom hostnames in dev.
- In containerized dev, prefer service names (`backend`, `redis`) over `localhost` for inter-service communication.

## PR Checklist

Before opening/merging a PR:

- [ ] Scope is focused and documented
- [ ] New/changed behavior has tests (or clear rationale if not)
- [ ] `pytest` passes (backend)
- [ ] `npm test`/coverage passes (frontend)
- [ ] Formatting/lint standards followed (black/isort, TS lint/style)
- [ ] Endpoint changes reflected in:
  - [ ] backend routes
  - [ ] `ENDPOINT_CATALOG` (`/api/catalog`)
  - [ ] `frontend/src/api.ts` endpoint map/client
- [ ] Local-first defaults preserved; external dependencies remain optional
- [ ] Docs updated (`README.md` and/or this file) when behavior changed

---

If you’re unsure, choose the option that improves reproducibility, local-first behavior, and clarity for the next contributor.