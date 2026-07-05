# SyncLine — full-stack version

Your original `SaaS.zip` was a single static `index.html`: all "sync" logic
(dedup, invoice generation, the 1,000-ops counter) ran in browser JavaScript
and vanished on every refresh. This adds a real backend underneath it and
wires the same frontend UI up to real API calls.

```
build/
  backend/    ← FastAPI + SQLAlchemy API (Python)
  frontend/   ← your original index.html, now calling the API
```

## What changed, and why this stack

You said you want this to double as practice for a data science / ML
engineering track — that's why the backend is **Python** (FastAPI +
SQLAlchemy) rather than Node: it's the same language ecosystem you'll use
for pandas, scikit-learn, PyTorch, etc., and FastAPI's type-hint-driven
style is close to how you'll write typed Python elsewhere. CSV parsing uses
**pandas** instead of hand-rolled string splitting — a small dose of the
tabular-data habits you'll use constantly later.

What you now have that the static demo didn't:

- **Real persistence** — Postgres (or SQLite for zero-setup local dev) instead of a JS `Map` that resets on refresh
- **Multi-tenant accounts** — signup/login (JWT), each organization only ever sees its own contacts/invoices
- **Server-side dedup + invoice generation** — same rules as before (dedupe by email, invoice only if amount > 0), now enforced by a DB unique constraint, not just JS logic anyone could bypass
- **Real integration hooks** — `backend/app/services/integrations/hubspot.py` and `quickbooks.py` make actual HubSpot/QuickBooks API calls once you connect real OAuth credentials; until then they no-op exactly like the old simulation
- **CSV export** streamed from the server's real invoice table

## Running it locally

### 1. Backend
```bash
cd backend
cp .env.example .env        # edit JWT_SECRET at minimum
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
This uses SQLite (`syncline.db`) by default — nothing else to install.
Interactive API docs: http://localhost:8000/docs

**Want Postgres instead** (closer to a real production setup)?
```bash
docker compose up --build
```
This starts Postgres + the API together, wired via `DATABASE_URL` in `docker-compose.yml`.

### 2. Frontend
```bash
cd frontend
python3 -m http.server 5500
```
Visit http://localhost:5500. The page will prompt you to sign up / log in
(that's expected — it's now a real multi-tenant app instead of an anonymous
demo). It talks to `http://localhost:8000` by default; change `API_BASE`
near the top of the `<script>` block in `index.html` if you deploy the API
elsewhere.

> I wasn't able to actually spin up and click through the running app in
> this environment (no outbound network access here to install the Python
> packages), so please run through signup → load sample → run sync →
> export once locally and tell me if anything misbehaves — I'll fix it fast.

## Going from "connected" to real HubSpot/QuickBooks data

1. Register a developer app with HubSpot / Intuit, get a client ID + secret
2. Put them in `backend/.env` (`HUBSPOT_CLIENT_ID`, etc.)
3. Click **Connect** next to that provider in the app — it's a real OAuth redirect
4. From then on, every sync run also pushes real contacts/deals/invoices to that provider

If you skip this, integrations just stay in "simulated" mode — the sync
still works, it just doesn't call out anywhere.

## Suggested next steps as you learn

- Swap `Base.metadata.create_all()` for **Alembic** migrations once the schema stabilizes
- Add rate limiting / refresh tokens to the auth flow before any real users touch it
- Add tests (`pytest` + `httpx.AsyncClient`) around `services/sync_engine.py` — it's the one piece of business logic worth locking down first
- If you want async DB access (good practice for I/O-bound APIs), migrate from `sqlalchemy.orm.Session` to `AsyncSession` + `asyncpg`
